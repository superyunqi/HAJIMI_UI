from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal

from core.annotation_mapper import to_overlay_items, ui_elements_to_inspect_items
from core.api_client import advance_step as api_advance_step
from core.coordinate_mapper import REF_H, REF_W
from core.prepare_guidance import resolve_prepare_scene
from core.screen_utils import capture_screen, capture_screen_cached, compute_fingerprint, downscale_for_api, get_locate_upload_max_side, get_upload_max_side, pil_to_data_uri, get_screen_metrics, get_upload_jpeg_quality


class AppController(QObject):
    """原生 UI 业务控制器 — 从 Bridge 提取，无 WebChannel 依赖"""

    message_added = pyqtSignal(str, str)
    steps_updated = pyqtSignal(list, int)
    status_updated = pyqtSignal(str, str)
    overlay_updated = pyqtSignal(list)
    overlay_cleared = pyqtSignal()
    inspect_updated = pyqtSignal(list, dict)
    inspect_cleared = pyqtSignal()
    inspect_status = pyqtSignal(str)
    blueprint_updated = pyqtSignal(list, int)
    suspension_requested = pyqtSignal(str)
    suspension_hidden = pyqtSignal()
    prepare_guidance_requested = pyqtSignal(dict)  # hint, desc, interaction, scene
    prepare_topmost_requested = pyqtSignal(bool)
    step_action_started = pyqtSignal(str)
    step_action_finished = pyqtSignal()
    mode_medium_requested = pyqtSignal()
    mode_compact_requested = pyqtSignal()

    def __init__(self, worker=None, step_worker=None, main_window=None):
        super().__init__(main_window)
        self._main_window = main_window
        self.worker = worker
        self.step_worker = step_worker
        self.task_id = None
        self.fingerprint = None
        self.steps = []
        self.current_step_index = 0
        self._screen_size = (REF_W, REF_H)
        self._ref_size = (REF_W, REF_H)
        self._screen_metrics = None
        self.ui_elements = []
        self._inspect_mode = False
        self._task_route: Optional[str] = None
        self._last_detection_meta: Optional[dict] = None
        self._relocate_fail_count = 0
        self._last_prepare_scene: Optional[dict] = None

        if self.worker:
            self.worker.sig_process_success.connect(self.on_process_success)
            self.worker.sig_process_error.connect(self.on_process_error)
            self.worker.sig_redline_triggered.connect(self.on_redline)

        if self.step_worker:
            self.step_worker.sig_step_success.connect(self._on_step_worker_success)
            self.step_worker.sig_step_error.connect(self._on_step_worker_error)

    def resize_window(self, width: int, height: int):
        win = self._main_window
        if not win:
            return
        width = max(280, int(width))
        height = max(52, int(height))
        geo = win.geometry()
        win.resize(width, height)
        win.move(geo.x() + geo.width() - width, geo.y() + geo.height() - height)

    def begin_window_drag(self):
        win = self._main_window
        if not win:
            return
        handle = win.windowHandle()
        if handle and hasattr(handle, "startSystemMove"):
            handle.startSystemMove()

    def submit_query(self, text: str):
        print(f"[Controller] 收到用户指令: {text}")
        self.exit_inspect_mode()
        self.message_added.emit(text, "user")
        self.status_updated.emit("processing", "AI 思考中...")
        self.overlay_cleared.emit()
        self.prepare_topmost_requested.emit(False)
        self.task_id = None
        self.steps = []
        self.current_step_index = 0
        self._task_route = None
        self._relocate_fail_count = 0
        self._last_prepare_scene = None

        if self.worker:
            if not self.worker.request_process(text):
                self.message_added.emit("请等待当前任务完成", "system")
                self.status_updated.emit("processing", "处理中...")
        else:
            self.message_added.emit("错误：任务线程未初始化", "system danger")
            self.status_updated.emit("idle", "准备就绪")

    def advance_step(self):
        print("[Controller] advance_step 被调用")
        self._request_step_action("advance")

    def skip_current_step(self):
        print("[Controller] skip_current_step 被调用")
        self._request_step_action("skip")

    def prev_step(self):
        if not self.task_id or not self.steps:
            self.message_added.emit("暂无步骤可回退", "system danger")
            return
        print("[Controller] prev_step 被调用")
        self._request_step_action("rollback")

    def resolve_suspension(self, action: str):
        print(f"[Controller] 挂起处理: {action}")
        self.suspension_hidden.emit()
        if action == "skip":
            self._request_step_action("skip")
        elif action == "rollback":
            self._request_step_action("rollback")
        elif action == "abort":
            self._request_step_action("terminate")

    def on_target_area_clicked(self):
        print("[Controller] 红框区域被点击")
        if not self.task_id or not self.steps:
            self.message_added.emit("请先等待任务生成步骤后再推进", "system danger")
            return
        if self.current_step_index >= len(self.steps):
            self.message_added.emit("已是最后一步", "system")
            return
        if self._current_step_needs_prepare():
            self.message_added.emit(
                "当前步骤需在 HAJIMI 面板点击「下一步」或「重新定位」，请勿点击桌面",
                "system",
            )
            return
        step = self.steps[self.current_step_index]
        ann = self._lookup_annotation(step)
        if not ann or not ann.get("highlight_bbox"):
            self.message_added.emit(
                "当前步骤尚无屏幕标注，请在面板中操作", "system"
            )
            return
        self.advance_step()

    def _refresh_fingerprint(self):
        screenshot = capture_screen()
        if screenshot is not None:
            self.fingerprint = compute_fingerprint(screenshot)

    def _on_step_worker_success(self, response: dict):
        self.step_action_finished.emit()
        self._handle_step_response(response)

    def _on_step_worker_error(self, error_msg: str):
        self.step_action_finished.emit()
        self.message_added.emit(f"步骤推进失败: {error_msg}", "system danger")
        self.status_updated.emit("executing", "正在指引中")

    def _request_step_action(self, action: str):
        if not self.task_id or not self.steps:
            print(
                f"[Controller] 步骤推进被拒绝: task_id={self.task_id}, "
                f"steps={len(self.steps)}"
            )
            self.message_added.emit("请先等待任务生成步骤后再推进", "system danger")
            return

        if self.step_worker and self.step_worker.isRunning():
            self.message_added.emit("步骤操作进行中，请稍候…", "system")
            return

        print(
            f"[Controller] 步骤推进: action={action}, "
            f"step={self.current_step_index + 1}/{len(self.steps)}"
        )
        step_index = self.current_step_index + 1

        if self.step_worker:
            self.step_action_started.emit(action)
            self.status_updated.emit("processing", "步骤推进中…")
            if not self.step_worker.request_step(
                self.task_id,
                step_index,
                self.fingerprint or "",
                action,
                self.steps,
                task_route=self._task_route,
            ):
                self.step_action_finished.emit()
                self.message_added.emit("步骤操作进行中，请稍候…", "system")
                self.status_updated.emit("executing", "正在指引中")
            return

        self._refresh_fingerprint()
        image_uri = None
        capture_size = None
        upload_size = None
        screen_metrics = None
        if action == "advance":
            shot, _ = capture_screen_cached(max_age_ms=900)
            if shot is None:
                shot = capture_screen()
            if shot is not None:
                nxt = (
                    self.steps[self.current_step_index + 1]
                    if self.current_step_index + 1 < len(self.steps)
                    else self.steps[self.current_step_index]
                )
                locate_text = " ".join(
                    filter(
                        None,
                        [
                            nxt.get("target"),
                            nxt.get("description"),
                            nxt.get("action"),
                        ],
                    )
                )
                upload = downscale_for_api(
                    shot, get_locate_upload_max_side(locate_text)
                )
                image_uri = pil_to_data_uri(upload, quality=get_upload_jpeg_quality())
                capture_size = [shot.size[0], shot.size[1]]
                upload_size = [upload.size[0], upload.size[1]]
                screen_metrics = get_screen_metrics()

        try:
            response = api_advance_step(
                self.task_id,
                step_index,
                self.fingerprint or "",
                action,
                self.steps,
                image_data_uri=image_uri,
                capture_size=capture_size,
                upload_size=upload_size,
                screen_metrics=screen_metrics,
            )
        except Exception as exc:
            self.message_added.emit(f"步骤推进失败: {exc}", "system danger")
            return

        self._handle_step_response(response)

    def _handle_step_response(self, response: dict):
        action = response.get("action", "")
        message = response.get("message") or ""

        if action == "suspended":
            self.suspension_requested.emit(
                message or "检测到屏幕状态与预期不符，您要跳过此步还是回退重试？"
            )
            self.status_updated.emit("suspended", "异常挂起")
            return

        if action == "terminated":
            self.message_added.emit("任务已终止。", "system danger")
            self.status_updated.emit("idle", "已终止")
            self.overlay_cleared.emit()
            return

        if action == "rollback":
            new_step = response.get("current_step", max(1, self.current_step_index))
            self.current_step_index = max(0, int(new_step) - 1)
            self._sync_frontend()
            self.message_added.emit(
                f"已回退到第 {self.current_step_index + 1} 步", "system"
            )
            self.status_updated.emit("executing", "正在指引中")
            return

        if action in ("advance", "skip"):
            prev_index = self.current_step_index
            new_step = response.get("current_step")
            if new_step is not None:
                self.current_step_index = max(0, int(new_step) - 1)
            else:
                self.current_step_index += 1

            next_step = self._coerce_step_dict(response.get("next_step"))
            if next_step and 0 <= self.current_step_index < len(self.steps):
                self.steps[self.current_step_index] = next_step

            self._apply_screen_context_from_response(response, next_step)

            blueprint_confirmed = (
                message == "蓝图已确认，开始执行"
                or (
                    prev_index == self.current_step_index
                    and "蓝图已确认" in message
                )
            )
            if (
                not blueprint_confirmed
                and prev_index < len(self.steps)
                and prev_index != self.current_step_index
            ):
                self.message_added.emit(
                    f"第 {prev_index + 1} 步已结束",
                    "system",
                )
            elif blueprint_confirmed:
                self.message_added.emit(
                    "已开始执行，请按第 1 步操作", "system"
                )

            if self.current_step_index < len(self.steps):
                desc = (
                    self.steps[self.current_step_index].get("description")
                    or self.steps[self.current_step_index].get("action", "")
                )
                self._sync_frontend()
                self._relocate_fail_count = 0
                if self._current_step_needs_prepare():
                    self._ensure_locate_failure_visible()
                else:
                    self.prepare_topmost_requested.emit(False)
                self.message_added.emit(
                    f"第 {self.current_step_index + 1} 步: {desc}",
                    "system",
                )
                self.status_updated.emit("executing", "正在指引中")
            else:
                self._finish_task()
            return

        if action == "complete":
            self._finish_task()
            return

        self.message_added.emit(f"未知步骤响应: {action}", "system danger")

    def _finish_task(self):
        if self.steps:
            frontend = self._frontend_steps()
            done_index = len(self.steps)
            self.steps_updated.emit(frontend, done_index)
            self.blueprint_updated.emit(frontend, done_index)
        self.message_added.emit("任务已结束", "system")
        self.status_updated.emit("idle", "已结束")
        self.overlay_cleared.emit()
        self._task_route = None
        self.mode_compact_requested.emit()

    def on_process_success(self, response, fingerprint):
        self.task_id = response.get("task_id")
        self.fingerprint = fingerprint
        meta = response.get("detection_meta") or {}
        self._task_route = meta.get("route")
        self._last_detection_meta = meta
        locator_first = meta.get("locator_first") or {}
        if locator_first:
            raw_out = str(locator_first.get("raw_locator_output", ""))[:120]
            print(
                f"[Controller] process locate: "
                f"reason={locator_first.get('locate_failure_reason')} "
                f"raw={raw_out!r}"
            )
        self._relocate_fail_count = 0
        self._last_prepare_scene = None
        self.steps = response.get("steps") or []
        self.ui_elements = response.get("ui_elements") or []
        self.current_step_index = 0
        self.exit_inspect_mode()

        size = response.get("_screen_size") or [REF_W, REF_H]
        self._screen_size = (int(size[0]), int(size[1]))
        if response.get("_mock"):
            self._ref_size = self._screen_size
        else:
            ref = (
                response.get("reference_resolution")
                or response.get("_ref_size")
                or size
            )
            self._ref_size = (int(ref[0]), int(ref[1]))
        self._screen_metrics = response.get("_screen_metrics")

        if self.task_id and self.steps and response.get("_mock"):
            register_task(self.task_id, self.steps)

        intent = response.get("intent") or {}
        summary = intent.get("summary", "操作指引")
        if response.get("_mock"):
            source_tag = " [Mock]"
        elif response.get("_source") == "server":
            source_tag = " [Server]"
        else:
            source_tag = ""
        self.message_added.emit(
            f"已理解意图「{summary}」，共 {len(self.steps)} 步{source_tag}",
            "system",
        )

        self._sync_frontend()
        self.status_updated.emit("executing", "正在指引中")
        self.blueprint_updated.emit(self._frontend_steps(), 0)

        if self.steps:
            self.mode_medium_requested.emit()

        self._ensure_locate_failure_visible()

    def _coerce_step_dict(self, step) -> Optional[dict]:
        if step is None:
            return None
        if isinstance(step, dict):
            return step
        if hasattr(step, "model_dump"):
            return step.model_dump()
        return None

    def _apply_screen_context_from_response(
        self,
        response: dict,
        next_step: Optional[dict] = None,
    ) -> None:
        size = response.get("_screen_size")
        if size and len(size) >= 2:
            self._screen_size = (int(size[0]), int(size[1]))
            print(f"[Controller] screen context updated: capture={self._screen_size}")

        metrics = response.get("_screen_metrics")
        if metrics:
            self._screen_metrics = metrics

        step = next_step
        if step is None and self.steps and 0 <= self.current_step_index < len(self.steps):
            step = self.steps[self.current_step_index]
        ann = self._lookup_annotation(step) if step else None
        if ann and ann.get("highlight_bbox"):
            self._ref_size = self._screen_size
            print(f"[Controller] ref_size synced to capture (L4 annotation)")
        else:
            ref = response.get("reference_resolution")
            if ref and len(ref) >= 2:
                self._ref_size = (int(ref[0]), int(ref[1]))

    def _ensure_locate_failure_visible(self) -> None:
        if not self.steps or not (0 <= self.current_step_index < len(self.steps)):
            return
        step = self.steps[self.current_step_index]
        if self._step_interaction(step) == "keyboard":
            return
        if not self._current_step_needs_prepare():
            return
        desc = step.get("description") or step.get("target") or step.get("action") or "目标元素"
        meta = self._last_detection_meta or {}
        locator_first = meta.get("locator_first") or {}
        failure_reason = locator_first.get("locate_failure_reason")
        print(
            f"[Controller] locate failure UX: step={desc!r} reason={failure_reason}"
        )
        self._notify_prepare_if_needed()

    def _step_interaction(self, step: dict) -> str:
        return step.get("interaction") or "screen"

    def _emit_prepare_guidance(self, step: dict) -> None:
        desc = step.get("description") or step.get("action", "")
        interaction = self._step_interaction(step)
        if interaction == "keyboard":
            self.prepare_topmost_requested.emit(False)
            self.message_added.emit(
                "请按步骤描述操作快捷键，完成后点击面板「下一步」",
                "system",
            )
            return

        hint = step.get("prepare_hint") or desc
        try:
            from core.assist_collect import gather_assist_bundle

            assist_bundle = gather_assist_bundle()
        except Exception:
            assist_bundle = None
        scene = resolve_prepare_scene(
            step,
            relocate_fail_count=self._relocate_fail_count,
            current_step_index=self.current_step_index,
            total_steps=len(self.steps),
            force_deferred=bool(step.get("locate_deferred")),
            assist_bundle=assist_bundle,
        )
        self._last_prepare_scene = scene.to_dict()
        self.prepare_topmost_requested.emit(True)
        self.prepare_guidance_requested.emit(
            {
                "hint": hint,
                "desc": desc,
                "interaction": interaction,
                "scene": self._last_prepare_scene,
            }
        )
        self.overlay_cleared.emit()
        self.message_added.emit(scene.body.split("\n")[0], "system")

    def _notify_prepare_if_needed(self):
        if not self._current_step_needs_prepare():
            self.prepare_topmost_requested.emit(False)
            return
        step = self.steps[self.current_step_index]
        self._emit_prepare_guidance(step)

    def _current_step_needs_prepare(self) -> bool:
        if not self.steps or not (0 <= self.current_step_index < len(self.steps)):
            return False
        step = self.steps[self.current_step_index]
        if self._step_interaction(step) == "keyboard":
            return False
        if step.get("locate_deferred"):
            return True
        ann = self._lookup_annotation(step)
        return not ann or not ann.get("highlight_bbox")

    def on_relocate_success(self, data: dict):
        self._relocate_fail_count = 0
        step_index = int(data.get("step_index", self.current_step_index + 1))
        idx = step_index - 1
        if 0 <= idx < len(self.steps):
            self.steps[idx]["annotation"] = data.get("annotation")
            self.steps[idx]["target_element_id"] = data.get("target_element_id")
            self.steps[idx]["locate_deferred"] = False
            self.steps[idx]["prepare_hint"] = None

        self.ui_elements = data.get("ui_elements") or self.ui_elements
        size = data.get("_screen_size") or data.get("reference_resolution")
        if size and len(size) >= 2:
            self._screen_size = (int(size[0]), int(size[1]))
        ref = data.get("reference_resolution") or data.get("_ref_size") or size
        if ref and len(ref) >= 2:
            self._ref_size = (int(ref[0]), int(ref[1]))
        self._screen_metrics = data.get("_screen_metrics") or self._screen_metrics

        self.message_added.emit(
            data.get("message") or "已根据新画面更新标注", "system"
        )
        self.prepare_topmost_requested.emit(False)
        self._sync_frontend()
        self.status_updated.emit("executing", "正在指引中")

    def on_relocate_error(self, error_msg: str):
        self._relocate_fail_count += 1
        self.message_added.emit(f"重新定位失败: {error_msg}", "system danger")
        self.status_updated.emit("executing", "正在指引中")
        if self.steps and 0 <= self.current_step_index < len(self.steps):
            step = self.steps[self.current_step_index]
            if self._current_step_needs_prepare():
                self._emit_prepare_guidance(step)

    def on_process_error(self, error_msg):
        print(f"[Controller] 处理错误: {error_msg}")
        self._task_route = None
        self.message_added.emit(f"处理失败: {error_msg}", "system danger")
        self.status_updated.emit("idle", "准备就绪")
        self.overlay_cleared.emit()

    def run_inspect(self):
        if self.worker and self.worker.isRunning():
            self.message_added.emit("请等待当前任务完成", "system danger")
            return False
        self.inspect_status.emit(
            "正在检测 UI 元素（CPU 约 2–4 分钟，请勿重复点击）…"
        )
        return True

    def on_inspect_success(self, data: dict):
        self._inspect_mode = True
        self.ui_elements = data.get("ui_elements") or []
        size = data.get("_screen_size") or data.get("reference_resolution") or [REF_W, REF_H]
        self._screen_size = (int(size[0]), int(size[1]))
        ref = data.get("reference_resolution") or size
        self._ref_size = (int(ref[0]), int(ref[1]))
        self._screen_metrics = data.get("_screen_metrics")

        meta = data.get("detection_meta") or {}
        count = meta.get("element_count", len(self.ui_elements))
        latency = meta.get("latency_ms", "?")
        backend = meta.get("backend", "unknown")
        self.inspect_status.emit(
            f"检验模式：{count} 个元素，{latency}ms，{backend}"
        )
        self.message_added.emit(
            f"检验完成：检测到 {count} 个 UI 元素（{latency}ms）",
            "system",
        )
        items = ui_elements_to_inspect_items(
            self.ui_elements,
            screen_size=self._screen_size,
            screen_metrics=self._screen_metrics,
        )
        self.inspect_updated.emit(items, meta)
        self.status_updated.emit("executing", "检验模式")

    def on_inspect_error(self, error_msg: str):
        self.inspect_status.emit(f"检验失败: {error_msg}")
        self.message_added.emit(f"检验失败: {error_msg}", "system danger")

    def exit_inspect_mode(self):
        if not self._inspect_mode:
            return
        self._inspect_mode = False
        self.inspect_cleared.emit()
        self.inspect_status.emit("")
        self.status_updated.emit("idle", "准备就绪")

    def on_redline(self, msg):
        print(f"[Controller] 红线触发: {msg}")
        self._task_route = None
        self.message_added.emit(msg, "system danger")
        self.status_updated.emit("idle", "已拦截")
        self.overlay_cleared.emit()

    def _lookup_annotation(self, step: dict) -> Optional[dict]:
        ann = step.get("annotation")
        if ann and ann.get("highlight_bbox"):
            return ann
        eid = step.get("target_element_id")
        if not eid:
            return ann
        for el in self.ui_elements:
            if el.get("element_id") == eid:
                bbox = el.get("bbox")
                if bbox:
                    return {
                        "type": "highlight_only",
                        "highlight_bbox": bbox,
                        "arrow_to": el.get("center"),
                    }
        return ann

    def _frontend_steps(self):
        return [
            {
                "desc": s.get("description") or s.get("action", ""),
                "action": s.get("action", ""),
                "annotation": s.get("annotation"),
            }
            for s in self.steps
        ]

    def _sync_frontend(self):
        frontend = self._frontend_steps()
        idx = min(self.current_step_index, max(0, len(self.steps) - 1))
        self.steps_updated.emit(frontend, idx)
        self.blueprint_updated.emit(frontend, idx)
        if self.steps and 0 <= self.current_step_index < len(self.steps):
            if self._current_step_needs_prepare():
                step = self.steps[self.current_step_index]
                ann = self._lookup_annotation(step)
                print(
                    f"[Overlay] step={self.current_step_index + 1} needs_prepare "
                    f"interaction={self._step_interaction(step)} "
                    f"bbox={ann.get('highlight_bbox') if ann else None}"
                )
                self.overlay_cleared.emit()
                return
            step = self.steps[self.current_step_index]
            annotation = self._lookup_annotation(step)
            items = to_overlay_items(
                annotation,
                self.current_step_index + 1,
                screen_size=self._screen_size,
                ref_size=self._ref_size,
                screen_metrics=self._screen_metrics,
            )
            bbox = annotation.get("highlight_bbox") if annotation else None
            print(
                f"[Overlay] step={self.current_step_index + 1} "
                f"screen={self._screen_size} ref={self._ref_size} "
                f"bbox={bbox} items={len(items)}"
            )
            if items:
                for item in items:
                    if item.get("type") == "box":
                        print(f"[Overlay]   rect={item.get('rect')}")
            elif bbox:
                print("[Overlay]   warn: bbox present but overlay items empty")
            self.overlay_updated.emit(items)
