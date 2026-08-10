"""
Research Crew — Day 1 "hello world" skeleton.

Goal for today: get ONE successful crew run on the board.
A Planner agent and a Writer agent run in sequence and produce
*some* output. No web search yet — that comes Friday.

Run with:  python -m research_crew.crew "your topic here"
"""

import sys
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

load_dotenv()  # Load ANTHROPIC_API_KEY from .env file if present

# --- Model -------------------------------------------------------------
# Using Sonnet 5 here; swap the model string if you prefer another.
llm = LLM(model="anthropic/claude-sonnet-5")


# --- Agents ------------------------------------------------------------
planner = Agent(
    role="Research Planner",
    goal="Break a topic into 3-5 focused, answerable research questions.",
    backstory=(
        "You are a meticulous research lead. You take a broad topic and "
        "decompose it into a short list of specific sub-questions that, "
        "if answered, would give someone a solid understanding of the topic."
    ),
    llm=llm,
    verbose=True,
)

writer = Agent(
    role="Report Writer",
    goal="Turn research questions and notes into a clear, structured brief.",
    backstory=(
        "You are a sharp technical writer. You take research questions and "
        "synthesize them into a readable markdown report with a short intro "
        "and one section per question."
    ),
    llm=llm,
    verbose=True,
)


# --- Tasks -------------------------------------------------------------
def build_tasks(topic: str):
    plan_task = Task(
        description=(
            f"The topic is: '{topic}'. Produce 3-5 focused research "
            "questions that would help someone understand this topic well. "
            "Return them as a numbered list, nothing else."
        ),
        expected_output="A numbered list of 3-5 research questions.",
        agent=planner,
    )

    write_task = Task(
        description=(
            f"Using the research questions for the topic '{topic}', write a "
            "short markdown brief. Include a one-paragraph intro, then one "
            "section per question with your best current understanding. "
            "This is a skeleton run — depth is not the point yet, structure is."
        ),
        expected_output="A markdown report with an intro and one section per question.",
        agent=writer,
        context=[plan_task],
    )

    return [plan_task, write_task]


# --- Crew --------------------------------------------------------------
def run(topic: str) -> str:
    crew = Crew(
        agents=[planner, writer],
        tasks=build_tasks(topic),
        process=Process.sequential,
        verbose=True,
    )
    result = crew.kickoff()
    return str(result)


if __name__ == "__main__":
    topic_arg = sys.argv[1] if len(sys.argv) > 1 else "The economic impact of remote work"
    print("\n" + "=" * 70)
    print(f"  RESEARCH CREW — topic: {topic_arg}")
    print("=" * 70 + "\n")

    output = run(topic_arg)

    print("\n" + "=" * 70)
    print("  FINAL REPORT")
    print("=" * 70 + "\n")
    print(output)