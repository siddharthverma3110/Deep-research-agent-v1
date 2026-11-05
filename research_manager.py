import asyncio

from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from academic_agent import academic_agent
from planner_agent import planner_agent, WebSearchItem, ResearchPlan, HOW_MANY_SEARCHES
from writer_agent import writer_agent, ReportData
from academic import search_papers
from sources import SourceRegistry, cite_web_result, finalize


class ResearchManager:
    async def run(self, query: str):
        """Yield ("status", text) events and finally ("report", {markdown, sources})."""
        registry = SourceRegistry()
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            yield ("status", f"Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield ("status", "Planning searches...")
            plan = await self.plan_searches(query)
            w, a = len(plan.web_searches), len(plan.academic_searches)
            yield ("status", f"Planned {w + a} searches ({w} web, {a} academic), running in parallel...")
            web, academic = await asyncio.gather(
                self.perform_web(plan.web_searches, registry),
                self.perform_academic(plan.academic_searches, registry),
            )
            yield ("status", "Searches complete, writing report...")
            report = await self.write_report(query, web, academic)
            markdown, sources = finalize(report.markdown_report, registry)
            yield ("report", {"markdown": markdown, "sources": sources})

    async def plan_searches(self, query: str) -> ResearchPlan:
        result = await Runner.run(planner_agent, f"Query: {query}")
        plan = result.final_output_as(ResearchPlan)
        plan.web_searches = plan.web_searches[:HOW_MANY_SEARCHES]
        plan.academic_searches = plan.academic_searches[:HOW_MANY_SEARCHES]
        return plan

    async def perform_web(self, items: list[WebSearchItem], registry: SourceRegistry) -> list[str]:
        results = await asyncio.gather(*(self.web_search(i, registry) for i in items))
        return [r for r in results if r]

    async def perform_academic(self, items: list[WebSearchItem], registry: SourceRegistry) -> list[str]:
        results = await asyncio.gather(*(self.academic_search(i, registry) for i in items))
        return [r for r in results if r]

    async def web_search(self, item: WebSearchItem, registry: SourceRegistry) -> str | None:
        prompt = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(search_agent, prompt)
            return f"Search: {item.query}\n{cite_web_result(result, registry)}"
        except Exception:
            return None

    async def academic_search(self, item: WebSearchItem, registry: SourceRegistry) -> str | None:
        papers = await search_papers(item.query)
        if not papers:
            return None
        lines = []
        for p in papers:
            s = registry.add("paper", p["title"], p["url"], authors=p["authors"], year=p["year"],
                             venue=p["venue"], cited_by=p["cited_by"], snippet=p["snippet"])
            meta = ", ".join(str(x) for x in (p["authors"], p["year"], p["venue"]) if x)
            lines.append(f"[{s.id}] {s.title} ({meta})\nAbstract: {p['abstract']}")
        prompt = (f"Search term: {item.query}\nReason for searching: {item.reason}\n\nPapers:\n"
                  + "\n\n".join(lines))
        try:
            result = await Runner.run(academic_agent, prompt)
            return f"Search: {item.query}\n{result.final_output}"
        except Exception:
            return None

    async def write_report(self, query: str, web: list[str], academic: list[str]) -> ReportData:
        prompt = (
            f"Original query: {query}\n\n"
            "## WEB SEARCH RESULTS\n" + ("\n\n".join(web) or "(none)") + "\n\n"
            "## ACADEMIC PAPER RESULTS\n" + ("\n\n".join(academic) or "(none: the academic search service returned no papers or was unavailable)")
        )
        result = await Runner.run(writer_agent, prompt)
        return result.final_output_as(ReportData)
