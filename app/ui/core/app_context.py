from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class AppContext:
    current_user: Optional[Dict[str, Any]] = None
    selected_product_id: Optional[str] = None
    selected_client_id: Optional[str] = None
