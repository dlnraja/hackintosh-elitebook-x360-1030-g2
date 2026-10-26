// Optional _OSI stand-in for I2C devices that stay hidden unless the
// firmware believes it is talking to Windows. Disabled in config.plist
// until the matching ACPI rename is enabled too.
//
// "Darwin" returns true so the other SSDTs in this folder keep their
// macOS gates after the rename. Do not call the real _OSI from here:
// once the rename is on, that call would recurse.
DefinitionBlock ("", "SSDT", 2, "X360G2", "XOSI", 0x00001000)
{
    Method (XOSI, 1, NotSerialized)
    {
        If ((Arg0 == "Darwin") || (Arg0 == "Windows 2009") || (Arg0 == "Windows 2012") || (Arg0 == "Windows 2013") || (Arg0 == "Windows 2015") || (Arg0 == "Windows 2016"))
        {
            Return (One)
        }
        Return (Zero)
    }
}
