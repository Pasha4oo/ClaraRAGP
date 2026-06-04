import re

from logs import logger
from ai.tool.tools import Tools

class ToolCaller(object):
    def __init__(self, app, ai_chat):
        self.tools = Tools(app, ai_chat)
        self.all_functions = {f.__name__: f for f in self.tools.all_functions}

    async def execute_tools(self, message: str) -> str:
        functions = re.findall(r"(\w+)\(([^)]*)\)", message)
    
        for function_name, function_params in functions:
            function = self.all_functions.get(function_name)

            if function_name is None:
                logger.error("Function not exist")
                continue

            kwargs = {k: v for k, v in re.findall(r"(\w+)\s*=\s*['\"]?(.*?)['\"]?(?=\s*,\s*\w+\s*=|['\"]?\s*$)", function_params)}
            
            logger.info(f"Function {function_name}({function_params}) founded")

            try:
                result = await function(**kwargs)
                logger.info("Execution was succsesfull")
                if result:
                    return result

            except NameError as e:
                logger.error(f"Error executing {function_name}({function_params})",  exc_info=True)

        return ""

    def remove_function_calls(self, message: str) -> str:
        return message.split('[', 1)[0]

