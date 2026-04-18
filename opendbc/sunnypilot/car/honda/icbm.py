"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""

from opendbc.car import structs, DT_CTRL
from opendbc.car.can_definitions import CanData
from opendbc.car.honda import hondacan
from opendbc.car.honda.values import CruiseButtons
from opendbc.sunnypilot.car.intelligent_cruise_button_management_interface_base import IntelligentCruiseButtonManagementInterfaceBase

ButtonType = structs.CarState.ButtonEvent.Type
SendButtonState = structs.IntelligentCruiseButtonManagement.SendButtonState

BUTTONS = {
  SendButtonState.increase: CruiseButtons.RES_ACCEL,
  SendButtonState.decrease: CruiseButtons.DECEL_SET,
}


class IntelligentCruiseButtonManagementInterface(IntelligentCruiseButtonManagementInterfaceBase):
  def __init__(self, CP, CP_SP):
    super().__init__(CP, CP_SP)

  def update(self, CC_SP, packer, frame, last_button_frame, CAN) -> list[CanData]:
    can_sends = []
    self.CC_SP = CC_SP
    self.ICBM = CC_SP.intelligentCruiseButtonManagement
    self.frame = frame
    self.last_button_frame = last_button_frame

    if self.ICBM.sendButton != SendButtonState.none:
      send_button = BUTTONS[self.ICBM.sendButton]

      # Send button press every frame (~10ms) to ensure Honda PCM registers it
      # between real SCM_BUTTONS messages from the steering column.
      # Hold for ~70ms (7 frames) then release for ~30ms (3 frames) to simulate
      # a realistic button press/release cycle that the PCM accepts.
      elapsed_frames = self.frame - self.last_button_frame
      cycle_pos = elapsed_frames % 10  # 10-frame cycle: 7 on, 3 off
      if cycle_pos < 7:
        can_sends.append(hondacan.spam_buttons_command(packer, CAN, send_button, self.CP.carFingerprint))
      if cycle_pos == 9:
        self.last_button_frame = self.frame + 1  # reset cycle

    return can_sends
