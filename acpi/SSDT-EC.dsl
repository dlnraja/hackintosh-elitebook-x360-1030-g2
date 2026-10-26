// Fake embedded-controller device for AppleBusPower on macOS.
// HID ACID0001 is intentional: it must not claim the real PNP0C09
// controller that battery and hotkeys use. _STA is zero outside Darwin
// so a Windows boot through OpenCore does not see this device.
// If boot fails with AE_ALREADY_EXISTS on EC, disable this SSDT.
DefinitionBlock ("", "SSDT", 2, "X360G2", "SsdtEC", 0x00001000)
{
    Scope (\_SB)
    {
        Device (EC)
        {
            Name (_HID, "ACID0001")
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
