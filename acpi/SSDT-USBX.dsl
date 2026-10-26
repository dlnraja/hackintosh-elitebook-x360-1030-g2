// USB power properties for Skylake and newer.
// 0x13EC (5100 mA) and 0x0834 (2100 mA) are the values shipped in
// OpenCore's SSDT-EC-USBX sample. They are a starting point, not a
// measurement of this laptop's ports.
DefinitionBlock ("", "SSDT", 2, "X360G2", "USBX", 0x00001000)
{
    Scope (\_SB)
    {
        Device (USBX)
        {
            Name (_ADR, Zero)
            Method (_DSM, 4, NotSerialized)
            {
                If (LEqual (Arg2, Zero))
                {
                    Return (Buffer (One) { 0x03 })
                }

                Return (Package (0x08)
                {
                    "kUSBSleepPowerSupply",
                    0x13EC,
                    "kUSBSleepPortCurrentLimit",
                    0x0834,
                    "kUSBWakePowerSupply",
                    0x13EC,
                    "kUSBWakePortCurrentLimit",
                    0x0834
                })
            }
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin"))
                {
                    Return (0x0F)
                }
                Return (Zero)
            }
        }
    }
}
