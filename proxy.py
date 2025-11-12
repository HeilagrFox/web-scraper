def get_proxy(config:dict)->None|str:
    proxy = None
    proxy_config = config.get('PROXY', {})
    if not proxy_config:
        return proxy
    if proxy_config.get("HTTPS"):
        proxy = f"{proxy_config['HTTPS']}"
    elif proxy_config.get("HTTP"):
        proxy = f"{proxy_config['HTTP']}" 
    return proxy
