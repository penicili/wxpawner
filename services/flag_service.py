from typing import List, Dict, Optional
import random
import string
from config.config import settings

class FlagService:
    @staticmethod
    def create_flag(flagStr: Optional[str] = None, assigned_team: str = "") -> Dict[str, str]:
        print (f"Creating flag with prefix: {settings.FLAG_PREFIX}, flagStr: {flagStr}, flagLength: {settings.FLAG_LENGTH}")
        if not flagStr:
            # Buat flag random jika tidak diberikan
            flagString = random.choices(string.ascii_letters + string.digits, k=settings.FLAG_LENGTH)
            flagString = f"{settings.FLAG_PREFIX}{{{''.join(flagString)}}}"
            return {"flag": flagString,
                    "assigned team": assigned_team}
        else:
            flagString = f"{settings.FLAG_PREFIX}{{{flagStr}}}"
            return {"flag": flagString,"assigned team": assigned_team}
