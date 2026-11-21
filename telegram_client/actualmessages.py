import threading
import queue

class ActualMessageMixin:
    def start_receiver(self):
        if self._receiver_running:
            return

        self._receiver_running = True

        self._receiver_thread = threading.Thread(
            target=self._receiver_loop,
            daemon=True
        )

        self._receiver_thread.start()

        print("Фоновый приём сообщений запущен.")


    def _receiver_loop(self):
        while self._receiver_running:
            update = self.receive(1.0)

            if not update:
                continue

            extra = update.get("@extra")

            if extra is not None:
                with self._pending_lock:
                    pending = self._pending_requests.get(str(extra))

                if pending is not None:
                    pending["result"] = update
                    pending["event"].set()
                    continue

            self.process_update(update)


    def get_message_event(self, timeout=None):
        try:
            return self.message_events.get(timeout=timeout)
        except queue.Empty:
            return None