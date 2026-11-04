// SPDX-License-Identifier: MIT OR Apache-2.0
//! Cooperative import cancellation. No worker thread is forcibly terminated.
use std::{
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
    time::{Duration, Instant},
};

#[derive(Clone, Default)]
pub struct ImportControl {
    cancelled: Arc<AtomicBool>,
    deadline: Option<Instant>,
    checkpoint_hook: Option<Arc<dyn Fn() + Send + Sync>>,
}

impl ImportControl {
    pub fn with_timeout(timeout: Duration) -> Self {
        Self {
            deadline: Instant::now().checked_add(timeout),
            ..Self::default()
        }
    }

    pub fn cancel(&self) {
        self.cancelled.store(true, Ordering::Release);
    }

    /// Observe safe import checkpoints on the thread doing the work. Callers
    /// may use this to apply a pending priority change. Keep the hook cheap:
    /// it can run on multiple Rayon workers and must never block or panic.
    pub fn with_checkpoint_hook(mut self, hook: impl Fn() + Send + Sync + 'static) -> Self {
        self.checkpoint_hook = Some(Arc::new(hook));
        self
    }

    /// Checked at import stages and between independent STEP shells. A parser
    /// call or one kernel shell operation already running must return first.
    pub fn check(&self) -> anyhow::Result<()> {
        if self.cancelled.load(Ordering::Acquire) {
            anyhow::bail!("model import cancelled");
        }
        if self
            .deadline
            .is_some_and(|deadline| Instant::now() >= deadline)
        {
            anyhow::bail!("model import exceeded its time budget");
        }
        if let Some(hook) = &self.checkpoint_hook {
            hook();
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cancellation_is_shared_by_clones_but_not_other_jobs() {
        let first = ImportControl::default();
        let clone = first.clone();
        std::thread::spawn(move || clone.cancel()).join().unwrap();
        assert!(first.check().unwrap_err().to_string().contains("cancelled"));
        assert!(ImportControl::default().check().is_ok());
    }

    #[test]
    fn an_expired_budget_stops_before_work() {
        let control = ImportControl::with_timeout(Duration::ZERO);
        assert!(
            control
                .check()
                .unwrap_err()
                .to_string()
                .contains("time budget")
        );
    }

    #[test]
    fn cancelled_step_does_not_parse_or_fall_back() {
        let control = ImportControl::default();
        control.cancel();
        let error = crate::step::parse_step_scene_with_control(
            b"not a STEP document",
            &mut crate::timing::Timings::default(),
            &control,
        )
        .err()
        .expect("cancelled imports must fail");
        assert!(error.to_string().contains("cancelled"));
    }

    #[test]
    fn checkpoint_hooks_run_on_the_import_thread() {
        let observed = Arc::new(std::sync::Mutex::new(None));
        let sink = observed.clone();
        let control = ImportControl::default().with_checkpoint_hook(move || {
            *sink.lock().unwrap() = Some(std::thread::current().id());
        });
        let worker = std::thread::spawn(move || {
            control.check().unwrap();
            std::thread::current().id()
        })
        .join()
        .unwrap();
        assert_eq!(*observed.lock().unwrap(), Some(worker));
    }
}
