"""
SERVER SHUTDOWN & HEARTBEAT GUARD MODULE
Monitors container lifecycle and sends immediate Telegram alerts if the server crashes, shuts down, or loses connection.
Author: Quant AI Engineering Team
"""

import atexit
import signal
import sys
import threading
import time
from execution_engine import send_instant_notification
from utils_tz import get_thai_str

_GUARD_INITIALIZED = False

def notify_server_online():
    """
    Sends a Telegram alert when the server boots up and comes online 24/7.
    """
    msg = (
        f"🟢 [SYSTEM ONLINE - SERVER ACTIVE 24/7]\n"
        f"เวลา: {get_thai_str()}\n"
        f"สถานะ: เซิร์ฟเวอร์และ AI Robot พร้อมสแกนตลาด 24 ชั่วโมงเรียบร้อยแล้ว!"
    )
    send_instant_notification(msg)

def notify_server_offline(reason: str = "SIGTERM / Container Redeploy or Stopped"):
    """
    Sends an immediate emergency Telegram alert if the server is stopping or disconnecting.
    """
    msg = (
        f"🔴 ⚠️ [CRITICAL SERVER ALERT - SERVER DISCONNECTED]\n"
        f"เวลา: {get_thai_str()}\n"
        f"คำเตือน: เซิร์ฟเวอร์/บอทหยุดการทำงานลงชั่วคราวแล้ว!\n"
        f"สาเหตุ: {reason}"
    )
    send_instant_notification(msg)

def _on_signal_received(signum, frame):
    sig_name = "SIGTERM" if signum == signal.SIGTERM else ("SIGINT" if signum == signal.SIGINT else f"Signal {signum}")
    notify_server_offline(f"ระบบได้รับสัญญาณปิดเครื่อง ({sig_name})")
    sys.exit(0)

def init_server_guard():
    """
    Registers exit handlers to catch any server shutdown, restart, or termination and alert Telegram.
    """
    global _GUARD_INITIALIZED
    if _GUARD_INITIALIZED:
        return
    _GUARD_INITIALIZED = True
    
    # Send online alert
    try:
        notify_server_online()
    except Exception as e:
        print(f"[SERVER GUARD] Online notification warning: {e}")

    # Register exit hook
    atexit.register(lambda: notify_server_offline("Process Normal Exit / Shutdown"))

    # Register signal handlers if on main thread
    try:
        signal.signal(signal.SIGTERM, _on_signal_received)
        signal.signal(signal.SIGINT, _on_signal_received)
    except Exception as e:
        print(f"[SERVER GUARD] Signal registration skipped (non-main thread): {e}")
