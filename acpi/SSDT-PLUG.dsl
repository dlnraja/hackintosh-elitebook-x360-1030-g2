// CPU plugin-type so XCPM can attach on Kaby Lake.
// Paths covered are the ones laptops of this era actually use.
// A path that is absent is skipped. This is the same idea as Acidanthera's
// SSDT-PLUG sample (OpenCorePkg, BSD-3-Clause); the text below is ours.
DefinitionBlock ("", "SSDT", 2, "X360G2", "CpuPlug", 0x00001000)
{
    External (_SB_.PR00, ProcessorObj)
    External (_SB_.CPU0, ProcessorObj)
    External (_PR_.CPU0, ProcessorObj)
    External (_PR_.PR00, ProcessorObj)

    Method (PLUG, 4, NotSerialized)
    {
        If (LEqual (Arg2, Zero))
        {
            Return (Buffer (One) { 0x03 })
        }

        Return (Package (0x02)
        {
            "plugin-type",
            One
        })
    }

    If (CondRefOf (\_SB.PR00))
    {
        Scope (\_SB.PR00)
        {
            Method (_DSM, 4, NotSerialized)
            {
                If (_OSI ("Darwin"))
                {
                    Return (PLUG (Arg0, Arg1, Arg2, Arg3))
                }
                Return (Buffer (One) { 0x00 })
            }
        }
    }

    If (CondRefOf (\_SB.CPU0))
    {
        Scope (\_SB.CPU0)
        {
            Method (_DSM, 4, NotSerialized)
            {
                If (_OSI ("Darwin"))
                {
                    Return (PLUG (Arg0, Arg1, Arg2, Arg3))
                }
                Return (Buffer (One) { 0x00 })
            }
        }
    }

    If (CondRefOf (\_PR.CPU0))
    {
        Scope (\_PR.CPU0)
        {
            Method (_DSM, 4, NotSerialized)
            {
                If (_OSI ("Darwin"))
                {
                    Return (PLUG (Arg0, Arg1, Arg2, Arg3))
                }
                Return (Buffer (One) { 0x00 })
            }
        }
    }

    If (CondRefOf (\_PR.PR00))
    {
        Scope (\_PR.PR00)
        {
            Method (_DSM, 4, NotSerialized)
            {
                If (_OSI ("Darwin"))
                {
                    Return (PLUG (Arg0, Arg1, Arg2, Arg3))
                }
                Return (Buffer (One) { 0x00 })
            }
        }
    }
}
