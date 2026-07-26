import json
from typing import Optional
from enterprise_os.runtime.goal import Goal
from enterprise_os.runtime.plan import Plan
from enterprise_os.runtime.step import Step, StepStatus
from enterprise_os.runtime.executive_session import ExecutiveSession
from enterprise_os.runtime.executive_state import ExecutiveState
from enterprise_os.runtime.decision import Decision, DecisionOutcome
from enterprise_os.runtime.events import EventDispatcher, GoalCreated, PlanGenerated, StepCompleted, StepFailed, StateTransitioned, DecisionMade, SessionFinished
from enterprise_os.runtime.persistence import SessionRepository
from enterprise_os.application.ports.ai_port import AIPort
from enterprise_os.application.ports.tool_port import ToolPort
from enterprise_os.providers.ai.capability import Capability
from enterprise_os.governance.approval_engine import ApprovalEngine

from enterprise_os.worker.worker_models import WorkItem
from enterprise_os.worker.worker_session import WorkerSession
from enterprise_os.worker.worker_loop import WorkerLoop

class ReasoningLoop:
    def __init__(
        self,
        ai_port: AIPort,
        tool_port: ToolPort,
        dispatcher: EventDispatcher,
        repository: SessionRepository,
        approval_engine: Optional[ApprovalEngine] = None,
    ) -> None:
        self.ai = ai_port
        self.tools = tool_port
        self.dispatcher = dispatcher
        self.repository = repository
        self.approval_engine = approval_engine
        self.worker_loop = WorkerLoop(ai_port, tool_port)

    def _transition(self, session: ExecutiveSession, new_state: ExecutiveState) -> None:
        old_state = session.context.state
        session.context.transition(new_state)
        self.dispatcher.dispatch(StateTransitioned(session_id=session.id, old_state=old_state.name, new_state=new_state.name))
        self.repository.save(session)

    def execute_goal(self, session: ExecutiveSession, goal: Goal) -> Decision:
        self.dispatcher.dispatch(GoalCreated(session_id=session.id, goal_id=goal.id, description=goal.description))
        self.repository.save(session)
        
        self._transition(session, ExecutiveState.PLANNING)
        plan = self._create_plan(goal, session)
        
        while True:
            import time
            time.sleep(0.5)
            step = plan.get_next_step()
            if not step:
                break
                
            self._transition(session, ExecutiveState.EXECUTING)
            self._execute_step(session, step)
            
            self._transition(session, ExecutiveState.REFLECTING)
            confidence_sufficient = self._reflect_on_step(session, step)
            
            if not confidence_sufficient:
                self._transition(session, ExecutiveState.RESEARCHING)
                self._research(step)
                
            plan.advance()
            self.repository.save(session)
            
        self._transition(session, ExecutiveState.DECIDING)
        
        failed_steps = [s for s in plan.steps if s.status == StepStatus.FAILED]
        if failed_steps:
            decision = Decision(outcome=DecisionOutcome.SEEK_APPROVAL, justification=f"Execution paused: {len(failed_steps)} step(s) failed.")
            if self.approval_engine is not None:
                approval_id = self.approval_engine.request_approval(
                    justification=decision.justification,
                    context=f"goal={goal.id} session={session.id} failed_steps={[s.id for s in failed_steps]}",
                )
                session.context.memory["pending_approval_id"] = approval_id
        else:
            decision = Decision(outcome=DecisionOutcome.PROCEED, justification="All steps completed successfully.")

        self.dispatcher.dispatch(DecisionMade(session_id=session.id, outcome=decision.outcome.name, justification=decision.justification))
        self.repository.save(session)
        
        self._transition(session, ExecutiveState.EVALUATING)
        from enterprise_os.runtime.events import EvaluationCompleted
        eval_prompt = f"Evaluate the execution of goal: {goal.description}. What went well? What failed? What should change next time?"
        eval_response = self.ai.request_capability(Capability.REFLECTION, eval_prompt)
        self.dispatcher.dispatch(EvaluationCompleted(session_id=session.id, reflection=eval_response.text))
        
        self.dispatcher.dispatch(SessionFinished(session_id=session.id))
        self.repository.save(session)
        
        return decision
        
    def _create_plan(self, goal: Goal, session: ExecutiveSession) -> Plan:
        prompt = f"""
You are the Digital CEO. Your goal is: {goal.description}
Break this down into an array of actionable steps.
Respond STRICTLY with this JSON format:
{{
    "steps": [
        {{"id": "1", "description": "do something"}},
        {{"id": "2", "description": "do next thing"}}
    ]
}}
"""
        response = self.ai.request_capability(Capability.PLANNING, prompt)
        
        try:
            raw = response.text.strip()
            if raw.startswith("```json"): raw = raw[7:]
            if raw.endswith("```"): raw = raw[:-3]
            
            data = json.loads(raw.strip())
            steps = [Step(id=str(s["id"]), description=s["description"]) for s in data.get("steps", [])]
            if not steps:
                steps = [Step(id="1", description="Fallback step due to empty JSON")]
        except Exception as e:
            steps = [Step(id="1", description=f"Fallback Step due to parsing error: {e}")]
            
        plan = Plan(id=f"plan-{goal.id}", goal_id=goal.id, steps=steps)
        self.dispatcher.dispatch(PlanGenerated(session_id=session.id, plan_id=plan.id, steps_count=len(plan.steps)))
        return plan
        
    def _execute_step(self, session: ExecutiveSession, step: Step) -> None:
        step.status = StepStatus.IN_PROGRESS
        
        worker_session = WorkerSession(objective=step.description)
        from enterprise_os.providers.tools.capability import ToolCapability
        work_item = WorkItem(
            id=f"wi-{step.id}", 
            objective=step.description,
            allowed_tools=[ToolCapability.PYTHON_EXECUTE, ToolCapability.SHELL_EXECUTE, ToolCapability.FILE_READ, ToolCapability.FILE_WRITE, ToolCapability.FILE_LIST],
            parameters={}
        )
        
        result = self.worker_loop.execute_work_item(worker_session, work_item)
        
        if result.success:
            step.result = result.findings
            step.status = StepStatus.COMPLETED
            self.dispatcher.dispatch(StepCompleted(session_id=session.id, step_id=step.id, result=result.findings))
        else:
            step.status = StepStatus.FAILED
            self.dispatcher.dispatch(StepFailed(session_id=session.id, step_id=step.id, error=result.findings))
            
    def _reflect_on_step(self, session: ExecutiveSession, step: Step) -> bool:
        return step.status == StepStatus.COMPLETED
        
    def _research(self, step: Step) -> None:
        pass
