from typing import List, Dict, Optional
import random
import string
from config.config import FLAG_PREFIX, FLAG_LENGTH

class FlagService:
    @staticmethod
    def create_flag(flagStr: Optional[str] = None, assigned_team: str = "") -> Dict[str, str]:
        print (f"Creating flag with prefix: {FLAG_PREFIX}, flagStr: {flagStr}, flagLength: {FLAG_LENGTH}")
        if not flagStr:
            # Buat flag random jika tidak diberikan
            flag = random.choices(string.ascii_letters + string.digits, k=FLAG_LENGTH)
            return {"flag": f"{FLAG_PREFIX}{{{''.join(flag)}}}",
                    "assigned team": assigned_team}

        return {"flag": f"{FLAG_PREFIX}{{{flagStr}}}",
                "assigned team": assigned_team}
