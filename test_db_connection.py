#!/usr/bin/env python3

import sys
sys.path.append('f:/0to100X/M2/AI_Agent/creator_pluse/backend')

try:
    from app.core.database import get_supabase
    from supabase import Client

    sb = get_supabase()
    print("Database connection successful")

    # Test the feedback table query that was failing
    result = sb.table("feedback").select("id").limit(1).execute()
    print(f"Feedback table accessible: {len(result.data)} records found")

except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
