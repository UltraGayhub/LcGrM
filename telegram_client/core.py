import json
import time
import threading

class CoreMixin:
    def send(self, data):
            request = json.dumps(
                data,
                ensure_ascii=False
            ).encode("utf-8")
    
            self.tdlib.td_json_client_send(
                self.client,
                request
            )
        
    def receive(self, timeout=1.0):
            result = self.tdlib.td_json_client_receive(
                self.client,
                timeout
            )
    
            if not result:
                return None
    
            try:
                return json.loads(result.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return None

    def close(self):
            if not self.client:
                return
    
            if self._receiver_running:
                # Просим TDLib закрыться
                self.send({"@type": "close"})
    
                # Ждём, пока фоновый поток получит подтверждение
                if not self._closed_event.wait(10):
                    print("Не дождались подтверждения закрытия TDLib.")
    
                # Останавливаем фоновый поток
                self._receiver_running = False
    
                if self._receiver_thread:
                    self._receiver_thread.join(timeout=3)
    
                    if self._receiver_thread.is_alive():
                        print("Ошибка: поток приёма не завершился.")
                        return
    
            else:
                # Если авторизация не завершилась и receiver ещё не запускался
                self.send({"@type": "close"})
    
                deadline = time.monotonic() + 10
    
                while time.monotonic() < deadline:
                    update = self.receive(0.5)
    
                    if update and update.get("@type") == "updateAuthorizationState":
                        state = update.get("authorization_state", {})
    
                        if state.get("@type") == "authorizationStateClosed":
                            break
    
            self.tdlib.td_json_client_destroy(self.client)
            self.client = None
    
            print("Telegram Client остановлен.")

    def request(self, data, timeout=30):
            if not self._receiver_running:
                raise RuntimeError("Фоновый приёмник TDLib не запущен.")
    
            with self._pending_lock:
                self.request_id += 1
                extra = str(self.request_id)
    
                waiter = {
                    "event": threading.Event(),
                    "result": None
                }
    
                self._pending_requests[extra] = waiter
    
            data["@extra"] = extra
    
            try:
                self.send(data)
    
                if not waiter["event"].wait(timeout):
                    raise TimeoutError(
                        f"Не дождались ответа: {data.get('@type')}"
                    )
    
                result = waiter["result"]
    
                if result.get("@type") == "error":
                    raise RuntimeError(
                        f"TDLib {result.get('code')}: "
                        f"{result.get('message')}"
                    )
    
                return result
    
            finally:
                with self._pending_lock:
                    self._pending_requests.pop(extra, None)
    
    