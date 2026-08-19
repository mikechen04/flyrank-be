import datetime

import inngest

from src.inngest_app.client import inngest_client
from src.reports.store import reports


@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello(ctx: inngest.Context) -> str:
    await ctx.step.sleep("wait-5s", datetime.timedelta(seconds=5))
    return "Hello from the background!"


@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(event="report/requested"),
    retries=2,
)
async def make_report(ctx: inngest.Context) -> dict:
    report_id = ctx.event.data["id"]
    topic = ctx.event.data["topic"]

    await ctx.step.sleep("do-the-slow-work", datetime.timedelta(seconds=8))

    def build() -> dict:
        if topic == "fail":
            raise Exception("The report oven is broken!")
        result = {
            "id": report_id,
            "topic": topic,
            "status": "done",
            "result": f"Report ready about: {topic}",
        }
        reports[report_id] = result
        return result

    return await ctx.step.run("build-report", build)


@inngest_client.create_function(
    fn_id="heartbeat",
    trigger=inngest.TriggerCron(cron="* * * * *"),
)
async def heartbeat(ctx: inngest.Context) -> str:
    def summary() -> str:
        pending = sum(1 for r in reports.values() if r.get("status") == "pending")
        done = sum(1 for r in reports.values() if r.get("status") == "done")
        failed = sum(1 for r in reports.values() if r.get("status") == "failed")
        line = f"heartbeat pending={pending} done={done} failed={failed}"
        print(line)
        return line

    line = await ctx.step.run("summary", summary)
    ctx.logger.info(line)
    return line
