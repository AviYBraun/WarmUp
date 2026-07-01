WarmUp
Try it out at: https://warmup.streamlit.app/
## Objective
In the new age of AI, integrating this technology to enhance—rather than hinder—learning is a massive challenge for all students, 
but none face it as acutely as Computer Science majors. In rigorous CS programs like those at the Technion, coding assignments often
throw you into the deep end, expecting you to simply "figure it out." When overwhelmed by the complexity, length, and strict 
deadlines of a project, the temptation to let an LLM simply write the code for you is immense. 
However, using AI as a crutch turns off your brain and hands over control to the machine.

That’s where WarmUp comes in.

The biggest hurdle when starting a complex project is a lack of hands-on experience with its individual components. You might
conceptually understand what a socket is, but if you’ve never written the code yourself, it's difficult to architect a network. 
When you multiply that by ten different required topics, cognitive overload sets in. You find yourself simultaneously trying
to gameplan a multi-part architecture while struggling to remember basic implementation syntax.

The best way to overcome this is by getting your hands dirty with smaller, muscle-memory tasks. Writing code yourself turns
hypothetical concepts into concrete understanding. Once you’ve built that technical muscle memory for the individual pieces, 
you can architect the broader project without getting bogged down by syntax and technicalities.

## What WarmUp Does
WarmUp bridges the gap between theoretical knowledge and practical implementation. It acts as an assignment prep-tool that breaks 
down massive coding projects into isolated, manageable exercises. Instead of doing the assignment for you, WarmUp analyzes your 
project requirements and generates targeted, LeetCode-style drills for the underlying concepts. It ensures you actually learn the
primitives needed to succeed before you tackle the main architecture.

## How It Works
1. **Extraction:** You upload your assignment instructions to the platform.
2. **Analysis:** The internal pipeline parses the text to isolate the core programming concepts, systems, and primitives required
   for the project.
4. **Drill Generation:** For each isolated concept, WarmUp loops through the AI agent to generate specific scaffolding, summaries,
   and bite-sized practice tests. 
6. **Preparation:** You practice these smaller tasks to build muscle memory, equipping you to handle the actual assignment with
   confidence and technical fluency.

## Roadmap (Future Updates)
This is currently an MVP, and there are several kinks to iron out. Planned updates include:
* **Performance Optimization:** Currently, loading summaries and test codes takes too long. I plan to add granular progress bars
* to show exactly what is running, and upgrade the pipeline to use the `asyncio` library to fire off simultaneous API calls,
* reducing wait times drastically.
* **Interactive Learning:** Allowing users to provide feedback on what they do or do not understand, prompting the agent to
* generate further rounds of targeted tests to iron out weak spots.
* **In-App Environment:** Integrating a live code editor and test runner so users can write and test their drills directly in the app.
* **Advanced Document Parsing:** Integrating OCR and image processing to handle complex PDFs and diagrams, rather than relying
* solely on raw text extraction.

## Lessons Learned Building with AI
* **Agents Can Exhaust Their Context:** Initially, I tried using a single API request to parse the PDF, extract concepts, and
* generate all exercises at once. This overwhelmed the agent, resulting in partial and insufficient outputs. I realized I had
* to orchestrate a loop: direct the program to retrieve the main topics first, then loop separate calls to the agent for each
* local test to preserve its attention frame.
* **You Must Lead the AI (Not the Other Way Around):** When dealing with bugs, AI assistants often suggest pushing forward with
* new tweaks or bloated code specifications to force an instant solution. You have to be willing to take a step back and fix the
*  root architecture. *Takeaway: You are the engineer; you must lead the agent.*
* **The Delegation Balance:** Building this required finding the sweet spot between maintaining control of the codebase and letting
*  the AI do the dirty work. You have to maximize efficiency by correctly identifying which tasks are true "busy work" to hand off,
*   and which require human logic and oversight.
