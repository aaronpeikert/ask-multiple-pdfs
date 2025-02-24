from langchain.agents import AgentExecutor
import prompts
from typing import Any, Dict, List, Optional, Tuple, Union

from langchain.agents.tools import InvalidTool
from langchain.callbacks.manager import (
    CallbackManagerForChainRun,
    Callbacks,
)
from langchain.schema import (
    AgentAction,
    AgentFinish,
    OutputParserException,
)
from langchain.tools.base import BaseTool
from langchain.agents.agent import ExceptionTool

class CustomExecutor(AgentExecutor):

    def _take_next_step(
        self,
        name_to_tool_map: Dict[str, BaseTool],
        color_mapping: Dict[str, str],
        inputs: Dict[str, str],
        intermediate_steps: List[Tuple[AgentAction, str]],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Union[AgentFinish, List[Tuple[AgentAction, str]]]:
        """Take a single step in the thought-action-observation loop.

        Override this to take control of how the agent makes and acts on choices.
        """
        try:
            intermediate_steps = self._prepare_intermediate_steps(intermediate_steps)

            # Call the LLM to see what to do.
            output = self.agent.plan(
                intermediate_steps,
                callbacks=run_manager.get_child() if run_manager else None,
                **inputs,
            )
        except OutputParserException as e:
            if isinstance(self.handle_parsing_errors, bool):
                raise_error = not self.handle_parsing_errors
            else:
                raise_error = False
            if raise_error:
                raise e
            text = str(e)
            if isinstance(self.handle_parsing_errors, bool):
                if e.send_to_llm:
                    observation = str(e.observation)
                    text = str(e.llm_output)
                else:
                    observation = "Invalid or incomplete response"
            elif isinstance(self.handle_parsing_errors, str):
                observation = self.handle_parsing_errors
            elif callable(self.handle_parsing_errors):
                observation = self.handle_parsing_errors(e)
            else:
                raise ValueError("Got unexpected type of `handle_parsing_errors`")
            output = AgentAction("_Exception", observation, text)
            if run_manager:
                run_manager.on_agent_action(output, color="green")
            tool_run_kwargs = self.agent.tool_run_logging_kwargs()
            observation = ExceptionTool().run(
                output.tool_input,
                verbose=self.verbose,
                color=None,
                callbacks=run_manager.get_child() if run_manager else None,
                **tool_run_kwargs,
            )
            return [(output, observation)]
        # If the tool chosen is the finishing tool, then we end and return.
        if isinstance(output, AgentFinish):
            return output
        actions: List[AgentAction]
        if isinstance(output, AgentAction):
            actions = [output]
        else:
            actions = output
        result = []
        try:
            for agent_action in actions:
                if run_manager:
                    run_manager.on_agent_action(agent_action, color="green")
                # Otherwise we lookup the tool
                if isinstance(agent_action, str):
                    observation = self.handle_parsing_errors
                    output = AgentAction("_Exception", observation, prompts.parsingError)
                    if run_manager:
                        run_manager.on_agent_action(output, color="green")
                    tool_run_kwargs = self.agent.tool_run_logging_kwargs()
                    observation = ExceptionTool().run(
                        output.tool_input,
                        verbose=self.verbose,
                        color=None,
                        callbacks=run_manager.get_child() if run_manager else None,
                        **tool_run_kwargs,
                    )
                    return [(output, observation)]
                    
                if agent_action.tool in name_to_tool_map:
                    tool = name_to_tool_map[agent_action.tool]
                    return_direct = tool.return_direct
                    color = color_mapping[agent_action.tool]
                    tool_run_kwargs = self.agent.tool_run_logging_kwargs()
                    if return_direct:
                        tool_run_kwargs["llm_prefix"] = ""
                    # We then call the tool on the tool input to get an observation
                    observation = tool.run(
                        agent_action.tool_input,
                        verbose=self.verbose,
                        color=color,
                        callbacks=run_manager.get_child() if run_manager else None,
                        **tool_run_kwargs,
                    )
                else:
                    tool_run_kwargs = self.agent.tool_run_logging_kwargs()
                    observation = InvalidTool().run(
                        agent_action.tool,
                        verbose=self.verbose,
                        color=None,
                        callbacks=run_manager.get_child() if run_manager else None,
                        **tool_run_kwargs,
                    )
                result.append((agent_action, observation))
        except OutputParserException as e:
            if isinstance(self.handle_parsing_errors, bool):
                raise_error = not self.handle_parsing_errors
            else:
                raise_error = False
            if raise_error:
                raise e
            text = str(e)
            if isinstance(self.handle_parsing_errors, bool):
                if e.send_to_llm:
                    observation = str(e.observation)
                    text = str(e.llm_output)
                else:
                    observation = "Invalid or incomplete response"
            elif isinstance(self.handle_parsing_errors, str):
                observation = self.handle_parsing_errors
            elif callable(self.handle_parsing_errors):
                observation = self.handle_parsing_errors(e)
            else:
                raise ValueError("Got unexpected type of `handle_parsing_errors`")
            output = AgentAction("_Exception", observation, text)
            if run_manager:
                run_manager.on_agent_action(output, color="green")
            tool_run_kwargs = self.agent.tool_run_logging_kwargs()
            observation = ExceptionTool().run(
                output.tool_input,
                verbose=self.verbose,
                color=None,
                callbacks=run_manager.get_child() if run_manager else None,
                **tool_run_kwargs,
            )
            return [(output, observation)]
        return result
