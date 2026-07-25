import importlib
import inspect
import pkgutil
from typing import Optional
from enterprise_os.providers.tools.provider import ToolProvider

class ToolRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ToolProvider] = {}
        
    def register_provider(self, provider: ToolProvider) -> None:
        self._providers[provider.name] = provider
        
    def get_provider(self, name: str) -> Optional[ToolProvider]:
        return self._providers.get(name)
        
    def list_providers(self) -> list[ToolProvider]:
        return list(self._providers.values())
        
    def clear(self) -> None:
        self._providers.clear()

    def auto_discover(self, module_name: str, **kwargs) -> None:
        import sys
        module = importlib.import_module(module_name)
        
        if not hasattr(module, '__path__'):
            return
            
        for _, name, _ in pkgutil.iter_modules(module.__path__):
            full_module_name = f"{module_name}.{name}"
            mod = importlib.import_module(full_module_name)
            
            for attr_name, attr_val in inspect.getmembers(mod, inspect.isclass):
                if attr_val is not ToolProvider and hasattr(attr_val, "name") and (hasattr(attr_val, "capabilities") or hasattr(attr_val, "can_handle")) and hasattr(attr_val, "execute"):
                    try:
                        sig = inspect.signature(attr_val.__init__)
                        init_kwargs = {}
                        for param_name, param in sig.parameters.items():
                            if param_name == 'self':
                                continue
                            if param_name in kwargs:
                                init_kwargs[param_name] = kwargs[param_name]
                            elif param.default == inspect.Parameter.empty and param.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                                break
                        else:
                            provider_instance = attr_val(**init_kwargs)
                            self.register_provider(provider_instance)
                    except Exception as e:
                        pass

