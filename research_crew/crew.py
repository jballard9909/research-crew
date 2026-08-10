"""
Research Crew — Three-agent research and report pipeline.

Given a topic, a Planner agent decomposes it into focused research
questions, a Web Researcher agent searches the web (via Serper) to find
sourced answers, and a Writer agent synthesizes the findings into a
structured markdown report with citations.

Run with:  python -m research_crew.crew "your topic here"
"""

import os
import re
import sys
from datetime import datetime

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool

load_dotenv()                     # Load ANTHROPIC_API_KEY and SERPER_API_KEY from .env file if present
search_tool = SerperDevTool()     # Initialize the Serper.dev search tool

# --- Model -------------------------------------------------------------
# Using Sonnet 5 here; swap the model string if you prefer another.
llm = LLM(model="anthropic/claude-sonnet-5", max_tokens=16000)  # Sized for large, cited reports; increase max_tokens if report truncates.


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

web_researcher = Agent(
    role="Web Researcher",
    goal="Find current, sourced, and relevant information to answer the research "
         "questions, prioritizing authoritative sources over unverified ones.",
    backstory=(
        "You are a skilled web researcher who verifies claims against real, "
        "reliable sources rather than from memory. You prioritize primary and "
        "authoritative sources — government data (.gov), academic and "
        "peer-reviewed research, established research institutions (e.g. NBER, "
        "Federal Reserve banks, universities), and reputable journalism. You "
        "avoid relying on forums, social media posts, or unverified blogs "
        "except as a last resort when no stronger source exists, and you note "
        "when a finding rests on a weaker source. You work efficiently: once "
        "you have 2-3 solid, well-sourced findings for a given research "
        "question, you move on rather than continuing to search for "
        "additional corroboration or chasing down a single source's exact "
        "wording."
    ),
    llm=llm,
    tools=[search_tool],
    verbose=True,
    max_iter=25,  # Hard cap on tool-call iterations. Without this, the agent
                  # has no enforced stopping point and will keep searching to
                  # verify granular details even after gathering enough
                  # material — observed burning 100+ Serper calls on a single
                  # research task before this was added.
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

    research_task = Task(
        description=(
            f"Using the research questions for the topic '{topic}', find "
            "current, sourced, and relevant information to answer each "
            "question. Prioritize authoritative sources — government data, "
            "peer-reviewed research, academic institutions, and established "
            "research organizations — over forums, social media, or blogs. "
            "If only a weaker source is available for a given point, note "
            "that explicitly rather than presenting it with the same "
            "confidence as a stronger source."
        ),
        expected_output="Answers to the research questions with source URLs "
                        "attached, noting source quality where relevant.",
        agent=web_researcher,
        context=[plan_task],
    )

    write_task = Task(
        description=(
            f"Using the sourced research findings for the topic '{topic}', write a "
            "markdown brief. Include a one-paragraph intro, then one "
            "section per question. Every claim must be grounded in the research findings — "
            "do not add information that wasn't found in the research. Cite the source "
            "URL for each claim."
        ),
        expected_output="A markdown report with an intro and one section per question, "
        "with source URLs cited for every substantive claim.",
        agent=writer,
        context=[plan_task, research_task],
    )

    return [plan_task, research_task, write_task]


# --- Output helpers ------------------------------------------------------
def slugify(topic: str, max_len: int = 50) -> str:
    """
    Convert a topic string into a filesystem-safe slug.

    Lowercases, replaces anything that isn't a letter/number with a hyphen,
    collapses repeated hyphens, and trims to max_len so long topics don't
    produce unwieldy filenames. Never trust user input in a filename, even
    in a CLI tool only you run.
    """
    slug = topic.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:max_len].rstrip("-")


def build_output_path(topic: str, outputs_dir: str = "outputs") -> str:
    """
    Build a sortable, collision-resistant output path:
    outputs/report_{topic-slug}_{timestamp}.md

    Timestamp format is sortable by filename (YYYY-MM-DD_HHMM) so a directory
    listing sorts chronologically without opening each file.
    """
    os.makedirs(outputs_dir, exist_ok=True)
    slug = slugify(topic)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"report_{slug}_{timestamp}.md"
    return os.path.join(outputs_dir, filename)


def build_metadata_header(topic: str, model_name: str) -> str:
    """
    Small metadata block written above the report body so a sample file in
    /examples is self-documenting without the README open in another tab.
    """
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        f"**Topic:** {topic}\n\n"
        f"**Generated:** {generated_at}\n\n"
        f"**Model:** {model_name}\n\n"
        "---\n\n"
    )


# --- Crew --------------------------------------------------------------
def run(topic: str) -> str:
    crew = Crew(
        agents=[planner, web_researcher, writer],
        tasks=build_tasks(topic),
        process=Process.sequential,
        verbose=True,
    )
    result = crew.kickoff()
    output = str(result)

    # Basic truncation check: a complete report should end with sentence-
    # ending punctuation, not cut off mid-word or mid-URL.
    if not output.rstrip().endswith((".", "!", "?", ")", "*")):
        print(
            "\n WARNING: Output may be truncated — it doesn't end with "
            "normal sentence punctuation. Check max_tokens on the LLM object.\n"
        )

    # Persist to disk. Metadata header + report body, kept separate by a
    # horizontal rule so the report itself stays clean if someone copies
    # just that part.
    output_path = build_output_path(topic)
    header = build_metadata_header(topic, llm.model)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write(output)
    print(f"\nSaved report to: {output_path}\n")

    return output


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