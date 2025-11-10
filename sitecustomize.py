# sitecustomize.py -- injected at interpreter startup when running lsg tests
# Purpose: if RUN_LSG_DELAY_MS is set to a non-negative integer, force movement
# and action delays in framework.objekt.Objekt to that value so tests run faster.
import os

try:
    _val = os.getenv('RUN_LSG_DELAY_MS')
    if _val is not None:
        try:
            RUN_LSG_DELAY_MS = int(_val)
        except Exception:
            RUN_LSG_DELAY_MS = -1
    else:
        RUN_LSG_DELAY_MS = -1
except Exception:
    RUN_LSG_DELAY_MS = -1

if RUN_LSG_DELAY_MS is not None and RUN_LSG_DELAY_MS >= 0:
    try:
        # Try to import the framework Objekt base class and monkeypatch common methods.
        from framework import objekt as _objmod
        _Objekt = getattr(_objmod, 'Objekt', None)
        if _Objekt is not None:
            def _make_wrapper(orig):
                def _wrapped(self, *args, **kwargs):
                    # Force delay_ms keyword if possible
                    try:
                        return orig(self, delay_ms=RUN_LSG_DELAY_MS)
                    except TypeError:
                        # If keyword not accepted, try positional
                        try:
                            return orig(self, RUN_LSG_DELAY_MS)
                        except Exception:
                            # Fallback to original call
                            return orig(self, *args, **kwargs)
                return _wrapped

            for _name in ('geh', 'zurueck', 'links', 'rechts', 'nehme_auf', 'nimm_herz'):
                if hasattr(_Objekt, _name):
                    try:
                        setattr(_Objekt, _name, _make_wrapper(getattr(_Objekt, _name)))
                    except Exception:
                        pass
    except Exception:
        # best-effort — if import fails do nothing
        pass
