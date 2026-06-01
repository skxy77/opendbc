from opendbc.car.carlog import carlog
from opendbc.car.isotp_parallel_query import IsoTpParallelQuery

EXT_DIAG_REQUEST = b'\x10\x03'
EXT_DIAG_RESPONSE = b'\x50\x03'

CLEAR_DTC_REQUEST = b'\x14\xFF\xFF\xFF'  # ClearDiagnosticInformation - all DTCs
CLEAR_DTC_RESPONSE = b'\x54'

CONTROL_DTC_OFF_REQUEST = b'\x85\x02'  # controlDTCSetting(OFF)
CONTROL_DTC_OFF_RESPONSE = b'\xC5\x02'


def clear_camera_dtc(can_recv, can_send, bus=0, addr=0x18DAB0F1, timeout=0.1, retry=5):
  """Clear DTCs from camera ECU to suppress CMBS/FCW dashboard alerts on radarless Honda.
  Also sets controlDTCSetting(OFF) to prevent new DTCs from being stored.
  Runs during init while panda is in ELM327 safety mode."""
  carlog.warning(f"clearing camera DTCs {hex(addr)} ...")

  for i in range(retry):
    try:
      # Step 1: Enter Extended Diagnostic session
      query = IsoTpParallelQuery(can_send, can_recv, bus, [(addr, None)], [EXT_DIAG_REQUEST], [EXT_DIAG_RESPONSE])
      for _, _ in query.get_data(timeout).items():
        # Step 2: Clear all DTCs
        carlog.warning("clearing all DTCs ...")
        query = IsoTpParallelQuery(can_send, can_recv, bus, [(addr, None)], [CLEAR_DTC_REQUEST], [CLEAR_DTC_RESPONSE])
        query.get_data(timeout)

        # Step 3: controlDTCSetting(OFF) - prevent new DTCs from being stored
        carlog.warning("disabling DTC storage ...")
        query = IsoTpParallelQuery(can_send, can_recv, bus, [(addr, None)], [CONTROL_DTC_OFF_REQUEST], [CONTROL_DTC_OFF_RESPONSE])
        query.get_data(timeout)

        carlog.warning("camera DTCs cleared successfully")
        return True

    except Exception:
      carlog.exception("clear camera DTC exception")

    carlog.error(f"clear camera DTC retry ({i + 1}) ...")

  carlog.error("clear camera DTC failed")
  return False
