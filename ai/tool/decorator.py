import json
import inspect
import re
from typing import Literal, get_args, get_origin

from docstring_parser import parse

registry = []

def tool(func):
    sig = inspect.signature(func)
    doc = parse(func.__doc__ or "")
    
    params_info = {}
    example_args = []

    for name, param in sig.parameters.items():
        if name in ('self', 'cls'):
            continue

        ds_param = next((p for p in doc.params if p.arg_name == name), None)
        description = ds_param.description if ds_param else "Нет описания"
        
        arg_type = param.annotation
        
        choices = None
        if get_origin(arg_type) is Literal:
            choices = list(get_args(arg_type))
            type_name = "enum"
            description += f" Допустимые значения: {choices}"
        else:
            type_name = getattr(arg_type, "__name__", str(arg_type))

        example_match = re.search(r"например,?\s*['\"]?([^'\".,)]+)['\"]?", description)
        if example_match:
            raw_example = example_match.group(1).strip()
        elif choices:
            raw_example = choices[0]
        else:
            raw_example = "..."

        if (arg_type == str or type_name == "enum") and raw_example != "...":
            example_val = f'{name}="{raw_example}"'
        else:
            example_val = f'{name}={raw_example}'
        example_args.append(example_val)

        is_required = param.default is inspect.Parameter.empty
        
        params_info[name] = {
            "type": type_name,
            "description": description,
            "required": is_required
        }
        if choices:
            params_info[name]["choices"] = choices
        if not is_required:
            params_info[name]["default"] = param.default

    tool_schema = {
        "function": func.__name__,
        "description": doc.short_description or "",
        "detailed_info": doc.long_description or "",
        "parameters": params_info,
        "syntax_template": f"[{func.__name__}({', '.join([f'{n}=...' for n in params_info])})]",
        "example_call": f"[{func.__name__}({', '.join(example_args)})]"
    }
    
    registry.append(tool_schema)
    return func