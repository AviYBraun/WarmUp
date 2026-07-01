import io
import os
import time
from pathlib import Path
from typing import List

import openai
import pdfplumber
import streamlit as st
from dotenv import load_dotenv
from openai import APIConnectionError, APITimeoutError, OpenAI, OpenAIError
from pydantic import BaseModel


MODEL_NAME = "gpt-4o-mini"
SAMPLE_PDF_NAME = "sample_assignment.pdf"


# 1. Load keys and initialize client
load_dotenv()


def get_openai_client() -> OpenAI:
    """Create an OpenAI client only when an API-backed pipeline step runs."""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
        except Exception:
            pass

    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is missing. Add it to your .env file or Streamlit secrets."
        )

    return OpenAI(api_key=api_key, timeout=30.0)


# 2. Define the exact JSON structure we want the AI to return
class ExtractionResult(BaseModel):
    primary_language: str
    primitives: List[str]


def extract_primitives(assignment_text: str) -> ExtractionResult:
    """Extract core CS concepts from assignment text into a validated schema."""
    if not assignment_text.strip():
        raise ValueError("Assignment text is empty; cannot extract primitives.")

    print("Agent 1: Extracting technical primitives...")

    system_prompt = """
You are a general computer science curriculum parser.
Extract the core programming concepts, algorithmic paradigms, design patterns,
language features, data structures, and system primitives required to complete
the assignment.

Also detect the primary programming language required for the assignment using
this exact logic:
1) Read the document for explicit instructions regarding the required coding
language.
2) If not explicitly stated, infer it from the libraries, syntax snippets, or
paradigms mentioned.
3) If it is completely ambiguous, default to 'Python or C++'.

Examples include dynamic programming, graph traversal, recursion, pointer
manipulation, interface implementation, class inheritance, file I/O, socket
creation, synchronization, memory allocation, parsing, hashing, testing, or
asymptotic analysis.

Return only the concepts required by the assignment. Keep each primitive short,
specific, and teachable. Output strictly according to the provided Pydantic
schema and include no extra prose.
""".strip()

    client = get_openai_client()

    try:
        completion = client.beta.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": assignment_text},
            ],
            response_format=ExtractionResult,
        )
    except (APITimeoutError, APIConnectionError) as exc:
        print(f"Error details: {exc}")
        raise RuntimeError("OpenAI request timed out or could not connect.") from exc
    except OpenAIError as exc:
        print(f"Error details: {exc}")
        raise RuntimeError("OpenAI extraction request failed.") from exc
    except Exception as exc:
        print(f"Error details: {exc}")
        raise RuntimeError("Failed to parse primitives into the expected schema.") from exc

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError("OpenAI returned no parsed extraction result.")

    return parsed


def generate_scaffolding(primitives: List[str], assignment_text: str) -> str:
    """Generate a concise conceptual guide that links concepts to the assignment."""
    if not primitives:
        raise ValueError("No primitives were provided for scaffolding.")
    if not assignment_text.strip():
        raise ValueError("Assignment text is empty; cannot generate scaffolding.")

    print("Agent 2: Generating conceptual scaffolding...")

    system_prompt = """
You are an elite Computer Science Teaching Assistant.
Create a brief, high-impact conceptual guide for a student preparing to solve
the assignment.

Connect the extracted concepts into one coherent mental model. Explain the
"why" behind the concepts and how they fit together in the assignment's larger
shape. Avoid full implementation steps, finished solutions, or overwhelming
detail. Keep the guidance general enough for any CS domain while still grounded
in the given assignment.
""".strip()

    user_prompt = f"""
Extracted concepts:
{", ".join(primitives)}

Assignment text:
{assignment_text}
""".strip()

    client = get_openai_client()

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )
    except (APITimeoutError, APIConnectionError) as exc:
        print(f"Error details: {exc}")
        raise RuntimeError("OpenAI request timed out or could not connect.") from exc
    except OpenAIError as exc:
        print(f"Error details: {exc}")
        raise RuntimeError("OpenAI scaffolding request failed.") from exc

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("OpenAI returned an empty scaffolding response.")

    return content.strip()


def generate_drills(
    primitives: List[str], primary_language: str, assignment_text: str = ""
) -> str:
    """Generate one isolated muscle-memory drill per extracted primitive."""
    if not primitives:
        raise ValueError("No primitives were provided for drill generation.")
    if not primary_language.strip():
        raise ValueError("Primary language is empty; cannot generate drills.")

    print("Agent 3: Generating isolated warm-up drills...")

    client = get_openai_client()
    drill_outputs: List[str] = []

    for index, primitive in enumerate(primitives, start=1):
        print(f"Agent 3.{index}: Generating drill for {primitive}...")

        system_prompt = f"""
You are generating a single, isolated LeetCode-style muscle-memory coding drill
for the concept: {primitive}.

You MUST write the entire drill in {primary_language}. The output must consist
of exactly two distinct parts: an empty Target Function and a complete Test
Harness.

Part 1: Target Function
- Generate an empty function signature for a focused micro-challenge that must
  be solved using {primitive}.
- Above the function, write a multi-line comment block defining the specific
  micro-challenge the student must solve using {primitive}.
- The inside of the function must be completely empty except for one comment:
  TODO: Implement your solution here
- You are strictly forbidden from writing any functional logic, boilerplate,
  helper calls, partial implementation, hints, or step-by-step guidance inside
  the Target Function itself.

Part 2: Test Harness
- Generate a complete main() function or language-equivalent entry point.
- The Test Harness must set up all dummy inputs, call the Target Function, and
  run assertions that verify the student's implementation behaves correctly.
- The Test Harness may contain complete setup and assertion logic, but it must
  not solve the target challenge on behalf of the student.

ANTI-CHEATING CONSTRAINT: You are strictly forbidden from writing ANY helper
functions, global variables, or structural logic outside of the main() function.
The generated code file MUST contain ONLY two things:
1. The empty Target Function signature and its instructional comment block.
2. The main() Test Harness function.
If the micro-challenge requires structs like a Queue or helper functions like a
worker thread, you MUST instruct the student to define them inside their TODO
block. DO NOT write them yourself.

Keep the drill small and focused on only this concept. Do not generate trivia,
explanations, prose after the code, or line-by-line TODO hints.
""".strip()

        user_prompt = f"""
Current primitive:
{primitive}

Detected primary language:
{primary_language}

Assignment context for language and domain inference:
{assignment_text or "No assignment text supplied."}
""".strip()

        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                )
                break
            except openai.RateLimitError as exc:
                print(f"Error details: {exc}")
                if attempt == max_retries:
                    raise RuntimeError(
                        f"OpenAI rate limit persisted while generating drill for {primitive}."
                    ) from exc

                wait_seconds = min(3 * (2 ** attempt), 30)
                print(f"Waiting {wait_seconds} seconds for rate limits...")
                time.sleep(wait_seconds)
            except (APITimeoutError, APIConnectionError) as exc:
                print(f"Error details: {exc}")
                raise RuntimeError(
                    f"OpenAI request timed out while generating drill for {primitive}."
                ) from exc
            except OpenAIError as exc:
                print(f"Error details: {exc}")
                raise RuntimeError(
                    f"OpenAI drill generation request failed for {primitive}."
                ) from exc
            except Exception as exc:
                print(f"Error details: {exc}")
                raise RuntimeError(
                    f"Unexpected drill generation failure for {primitive}."
                ) from exc

        content = response.choices[0].message.content
        if not content:
            raise RuntimeError(f"OpenAI returned an empty drill for {primitive}.")

        drill_outputs.append(f"## Drill {index}: {primitive}\n\n{content.strip()}")

    return "\n\n".join(drill_outputs)


def extract_text_from_pdf(pdf_path_or_bytes: object) -> str:
    """Extract readable text from a PDF and return it as a clean single string."""
    if isinstance(pdf_path_or_bytes, (str, Path)):
        path = Path(pdf_path_or_bytes).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")
        if not path.is_file():
            raise ValueError(f"PDF path is not a file: {path}")
        pdf_source = path
        source_label = str(path)
    elif isinstance(pdf_path_or_bytes, bytes):
        pdf_source = io.BytesIO(pdf_path_or_bytes)
        source_label = "uploaded PDF bytes"
    elif hasattr(pdf_path_or_bytes, "getvalue"):
        pdf_source = io.BytesIO(pdf_path_or_bytes.getvalue())
        source_label = "uploaded PDF file"
    elif hasattr(pdf_path_or_bytes, "read"):
        pdf_source = io.BytesIO(pdf_path_or_bytes.read())
        source_label = "uploaded PDF stream"
    else:
        raise TypeError("Expected a PDF path, bytes, or file-like object.")

    try:
        page_texts: List[str] = []
        with pdfplumber.open(pdf_source) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                cleaned = " ".join(text.split())
                if cleaned:
                    page_texts.append(cleaned)
                else:
                    print(f"Warning: no extractable text found on page {page_number}.")
    except Exception as exc:
        raise RuntimeError(f"Failed to extract text from PDF: {source_label}") from exc

    extracted_text = "\n\n".join(page_texts).strip()
    if not extracted_text:
        raise ValueError(f"No extractable text found in PDF: {source_label}")

    return extracted_text


def run_pipeline(assignment_text: str) -> tuple[ExtractionResult, str, str]:
    """Run the stateless extraction, scaffolding, and drill-generation pipeline."""
    extraction = extract_primitives(assignment_text)
    scaffolding = generate_scaffolding(extraction.primitives, assignment_text)
    drills = generate_drills(
        extraction.primitives, extraction.primary_language, assignment_text
    )
    return extraction, scaffolding, drills


def run_full_pipeline(pdf_path_or_bytes: object) -> dict:
    """Extract PDF text, run all AI agents, and return UI-ready results."""
    assignment_text = extract_text_from_pdf(pdf_path_or_bytes)
    extraction, scaffolding, drills = run_pipeline(assignment_text)

    return {
        "primary_language": extraction.primary_language,
        "primitives": extraction.primitives,
        "scaffolding": scaffolding,
        "drills": drills,
    }


def print_section(title: str, content: str) -> None:
    print(f"\n{'=' * 80}")
    print(title)
    print("=" * 80)
    print(content)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    sample_pdf_path = project_root / SAMPLE_PDF_NAME

    try:
        print(f"Loading assignment PDF: {sample_pdf_path}")
        result = run_full_pipeline(str(sample_pdf_path))

        print_section(
            "Detected Primary Language",
            result["primary_language"],
        )
        print_section(
            "Step 1: Extracted Technical Primitives",
            "\n".join(f"- {primitive}" for primitive in result["primitives"]),
        )
        print_section("Step 2: Conceptual Scaffolding", result["scaffolding"])
        print_section("Step 3: Warm-Up Code Drills", result["drills"])
    except Exception as exc:
        print(f"\nPipeline failed: {exc}")
