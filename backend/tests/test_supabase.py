from app.db import ping_supabase


def test_supabase_ping():
    assert ping_supabase() is True
