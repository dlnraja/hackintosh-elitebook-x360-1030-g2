// Backlight device for WhateverGreen.
// _UID 16 selects the Skylake/Kaby Lake PWM profile (PWMMax 0x56c)
// described in WhateverGreen. This is only the device stub. It does not
// include the RehabMan PNLF register program, which is GPL-2.0.
DefinitionBlock ("", "SSDT", 2, "X360G2", "PNLF", 0x00001000)
{
    Scope (\_SB)
    {
        Device (PNLF)
        {
            Name (_HID, EisaId ("APP0002"))
            Name (_CID, "backlight")
            Name (_UID, 16)
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin"))
                {
                    Return (0x0B)
                }
                Return (Zero)
            }
        }
    }
}
