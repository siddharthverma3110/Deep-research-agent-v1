import asyncio

from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData


class ResearchManager:
    async def run(self, query: str):
        """Run the deep research process, yielding ("status", text) events and finally ("report", markdown)."""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            yield ("status", f"Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield ("status", "Planning searches...")
            search_plan = await self.plan_searches(query)
            yield ("status", f"Planned {len(search_plan.searches)} searches, running in parallel...")
            search_results = await self.perform_searches(search_plan)
            yield ("status", "Searches complete, writing report...")
            report = await self.write_report(query, search_results)
            yield ("report", report.markdown_report)

    async def plan_searches(self, query: str) -> WebSearchPlan:
        result = await Runner.run(planner_agent, f"Query: {query}")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, plan: WebSearchPlan) -> list[str]:
        tasks = [asyncio.create_task(self.search(item)) for item in plan.searches]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    async def search(self, item: WebSearchItem) -> str | None:
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(search_agent, input)
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(writer_agent, input)
        return result.final_output_as(ReportData)
