from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "You are a senior researcher writing a cohesive, detailed report (at least 1000 words, markdown) for a research "
    "query. You are given summaries from WEB SEARCH RESULTS and from ACADEMIC PAPER RESULTS. Plan an outline first, "
    "then write the report with exactly these top-level sections, using ## headings:\n"
    "## Summary - a short overview of the answer.\n"
    "## Findings from Web Sources - built from the web search results.\n"
    "## Findings from Academic Papers - built from the academic paper results.\n"
    "## Synthesis - how the web and academic evidence agree, differ, and what remains uncertain.\n\n"
    "CITATIONS: the research text contains markers like [12]. Cite in-text by placing the marker right after the "
    "claim it supports, exactly as written, using separate brackets for several sources, e.g. [3][8] (never [3, 8]). "
    "Only use markers that appear in the research text, never invent or alter numbers, and do not cite a source for "
    "something it does not support. Do not write a references or bibliography section; it is generated automatically. "
    "If one of the two evidence types is empty, say so briefly in its section."
)


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The final report, with [n] citation markers.")
    follow_up_questions: list[str] = Field(description="Suggested topics to research further.")


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
)
