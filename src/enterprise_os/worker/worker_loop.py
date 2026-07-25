import json
from enterprise_os.worker.worker_models import WorkItem, StructuredResult
from enterprise_os.worker.worker_session import WorkerSession
from enterprise_os.application.ports.tool_port import ToolPort
from enterprise_os.application.ports.ai_port import AIPort
from enterprise_os.providers.ai.capability import Capability

class WorkerLoop:
    def __init__(self, ai_port: AIPort, tool_port: ToolPort) -> None:
        self.ai = ai_port
        self.tools = tool_port

    def execute_work_item(self, session: WorkerSession, work_item: WorkItem) -> StructuredResult:
        capabilities_list = [cap.name for cap in work_item.allowed_tools]
        prompt = f"""
You are an execution worker. Your objective is: {work_item.objective}
You have access to the following capabilities: {capabilities_list}

Select the most appropriate capability to achieve the objective.
Provide your response strictly in the following JSON format, with no markdown formatting or extra text:
{{
    "capability": "NAME_OF_CAPABILITY",
    "arguments": {{
        "arg1": "value1"
    }}
}}
"""
        response = self.ai.request_capability(
            capability=Capability.TOOL_SELECTION,
            prompt=prompt
        )
        
        try:
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            
            decision = json.loads(raw_text.strip())
            cap_name = decision.get("capability")
            tool_args = decision.get("arguments", {})
            
            from enterprise_os.providers.tools.capability import ToolCapability
            selected_capability = ToolCapability.from_string(cap_name) if cap_name else None
            
        except Exception as e:
            return StructuredResult(
                work_item_id=work_item.id,
                success=False,
                findings=f"Failed to parse AI capability decision: {str(e)}\nRaw Response: {response.text}"
            )
            
        if not selected_capability or selected_capability not in work_item.allowed_tools:
            return StructuredResult(
                work_item_id=work_item.id,
                success=False,
                findings=f"CapabilityResolutionFailed: AI selected capability '{cap_name}' which is not in allowed capabilities: {capabilities_list}"
            )
            
        try:
            resp = self.tools.execute_tool(selected_capability, tool_args)
            return StructuredResult(
                work_item_id=work_item.id,
                success=resp.success,
                findings=str(resp.result) if resp.success else resp.error_message,
                artifacts={"execution_time": resp.execution_time}
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return StructuredResult(
                work_item_id=work_item.id,
                success=False,
                findings=f"Worker failed to execute tool: {str(e)}"
            )
