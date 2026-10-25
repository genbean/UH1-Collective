# hsr-usb-lib.ps1 - shared helpers for the HeliSR test scripts: the HID
# settings channel, settings read/write, and Windows' joystick API.
# Dot-source it:  . (Join-Path $PSScriptRoot 'hsr-usb-lib.ps1')
#
# Part of HeliSR. Copyright (C) 2026 HeliSR contributors. GPL-3.0-or-later.

if (-not ([System.Management.Automation.PSTypeName]'Hsr').Type) {
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

public class HsrDev
{
    public string Path, Product, Serial, Manufacturer;
    public ushort Vid, Pid, Version, UsagePage, Usage, InLen, OutLen;
}

public static class Hsr
{
    [StructLayout(LayoutKind.Sequential)]
    struct SP_DEVICE_INTERFACE_DATA { public int cbSize; public Guid InterfaceClassGuid; public int Flags; public IntPtr Reserved; }
    [StructLayout(LayoutKind.Sequential)]
    struct HIDD_ATTRIBUTES { public int Size; public ushort VendorID, ProductID, VersionNumber; }
    [StructLayout(LayoutKind.Sequential)]
    struct HIDP_CAPS
    {
        public ushort Usage, UsagePage, InputReportByteLength, OutputReportByteLength, FeatureReportByteLength;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 17)] public ushort[] Reserved;
        public ushort NumberLinkCollectionNodes, NumberInputButtonCaps, NumberInputValueCaps, NumberInputDataIndices,
            NumberOutputButtonCaps, NumberOutputValueCaps, NumberOutputDataIndices,
            NumberFeatureButtonCaps, NumberFeatureValueCaps, NumberFeatureDataIndices;
    }

    [DllImport("hid.dll")] static extern void HidD_GetHidGuid(out Guid g);
    [DllImport("hid.dll")] static extern bool HidD_GetAttributes(SafeFileHandle h, ref HIDD_ATTRIBUTES a);
    [DllImport("hid.dll")] static extern bool HidD_GetPreparsedData(SafeFileHandle h, out IntPtr p);
    [DllImport("hid.dll")] static extern bool HidD_FreePreparsedData(IntPtr p);
    [DllImport("hid.dll")] static extern int HidP_GetCaps(IntPtr p, ref HIDP_CAPS c);
    [DllImport("hid.dll")] static extern bool HidD_GetProductString(SafeFileHandle h, byte[] b, int len);
    [DllImport("hid.dll")] static extern bool HidD_GetSerialNumberString(SafeFileHandle h, byte[] b, int len);
    [DllImport("hid.dll")] static extern bool HidD_GetManufacturerString(SafeFileHandle h, byte[] b, int len);
    [DllImport("setupapi.dll", SetLastError = true)] static extern IntPtr SetupDiGetClassDevs(ref Guid g, IntPtr e, IntPtr w, int flags);
    [DllImport("setupapi.dll", SetLastError = true)] static extern bool SetupDiEnumDeviceInterfaces(IntPtr set, IntPtr info, ref Guid g, int i, ref SP_DEVICE_INTERFACE_DATA d);
    [DllImport("setupapi.dll", SetLastError = true, CharSet = CharSet.Unicode)] static extern bool SetupDiGetDeviceInterfaceDetail(IntPtr set, ref SP_DEVICE_INTERFACE_DATA d, IntPtr detail, int size, out int req, IntPtr info);
    [DllImport("setupapi.dll")] static extern bool SetupDiDestroyDeviceInfoList(IntPtr set);
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)] static extern SafeFileHandle CreateFile(string n, uint access, uint share, IntPtr sec, uint disp, uint flags, IntPtr t);

    static string Str(byte[] b) { string s = Encoding.Unicode.GetString(b); int z = s.IndexOf('\0'); return z >= 0 ? s.Substring(0, z) : s; }

    public static List<HsrDev> List()
    {
        var list = new List<HsrDev>();
        Guid g; HidD_GetHidGuid(out g);
        IntPtr set = SetupDiGetClassDevs(ref g, IntPtr.Zero, IntPtr.Zero, 0x12);   // PRESENT | DEVICEINTERFACE
        try
        {
            for (int i = 0; ; i++)
            {
                var d = new SP_DEVICE_INTERFACE_DATA(); d.cbSize = Marshal.SizeOf(d);
                if (!SetupDiEnumDeviceInterfaces(set, IntPtr.Zero, ref g, i, ref d)) break;
                int req; SetupDiGetDeviceInterfaceDetail(set, ref d, IntPtr.Zero, 0, out req, IntPtr.Zero);
                IntPtr buf = Marshal.AllocHGlobal(req);
                try
                {
                    Marshal.WriteInt32(buf, IntPtr.Size == 8 ? 8 : 6);
                    if (!SetupDiGetDeviceInterfaceDetail(set, ref d, buf, req, out req, IntPtr.Zero)) continue;
                    string path = Marshal.PtrToStringUni(new IntPtr(buf.ToInt64() + 4));
                    using (var h = CreateFile(path, 0, 3, IntPtr.Zero, 3, 0, IntPtr.Zero))
                    {
                        if (h.IsInvalid) continue;
                        var a = new HIDD_ATTRIBUTES(); a.Size = Marshal.SizeOf(a);
                        if (!HidD_GetAttributes(h, ref a)) continue;
                        var dev = new HsrDev { Path = path, Vid = a.VendorID, Pid = a.ProductID, Version = a.VersionNumber };
                        IntPtr pp;
                        if (HidD_GetPreparsedData(h, out pp))
                        {
                            var c = new HIDP_CAPS(); HidP_GetCaps(pp, ref c); HidD_FreePreparsedData(pp);
                            dev.UsagePage = c.UsagePage; dev.Usage = c.Usage; dev.InLen = c.InputReportByteLength; dev.OutLen = c.OutputReportByteLength;
                        }
                        byte[] s = new byte[256];
                        if (HidD_GetProductString(h, s, s.Length)) dev.Product = Str(s);
                        s = new byte[256]; if (HidD_GetSerialNumberString(h, s, s.Length)) dev.Serial = Str(s);
                        s = new byte[256]; if (HidD_GetManufacturerString(h, s, s.Length)) dev.Manufacturer = Str(s);
                        list.Add(dev);
                    }
                }
                finally { Marshal.FreeHGlobal(buf); }
            }
        }
        finally { SetupDiDestroyDeviceInfoList(set); }
        return list;
    }

    // ------------------------------------------------- settings channel --

    static FileStream fs;
    static Task<int> pending;
    static byte[] rbuf = new byte[64];

    public static void Open(string path)
    {
        var h = CreateFile(path, 0xC0000000, 3, IntPtr.Zero, 3, 0x40000000, IntPtr.Zero);   // read/write, overlapped
        if (h.IsInvalid) throw new IOException("Can't open " + path + " (error " + Marshal.GetLastWin32Error() + ")");
        fs = new FileStream(h, FileAccess.ReadWrite, 64, true);
        pending = null;
    }

    public static void Close() { if (fs != null) { try { fs.Dispose(); } catch { } fs = null; } }

    static byte[] ReadPacket(int timeoutMs)
    {
        if (pending == null) pending = fs.ReadAsync(rbuf, 0, 64);
        if (!pending.Wait(timeoutMs)) return null;
        int n = pending.Result; pending = null;
        if (n <= 0) return null;
        var p = new byte[64]; Array.Copy(rbuf, p, Math.Min(n, 64));
        return p;
    }

    // Send a command; return the reply (same command and index) or null on timeout.
    public static byte[] Transact(byte cmd, byte index, byte[] data, int timeoutMs)
    {
        var p = new byte[64];
        p[0] = 2; p[1] = cmd; p[2] = index;
        if (data != null) Array.Copy(data, 0, p, 4, Math.Min(data.Length, 60));
        fs.Write(p, 0, 64);
        var t0 = DateTime.Now;
        while ((DateTime.Now - t0).TotalMilliseconds < timeoutMs)
        {
            var r = ReadPacket(timeoutMs);
            if (r == null) return null;
            if (r[0] == 2 && r[1] == cmd && r[2] == index) return r;
        }
        return null;
    }

    static byte[] Hex(string h)
    {
        var b = new byte[h.Length / 2];
        for (int i = 0; i < b.Length; i++) b[i] = Convert.ToByte(h.Substring(2 * i, 2), 16);
        return b;
    }

    // Lockstep (test firmware): send each "step <inputs> <expected>" line's
    // inputs as TEST_STEP and compare the 43 result bytes. Returns null if all
    // match, or a description of the first difference. done = steps checked.
    public static string StepAll(string[] lines, out int done)
    {
        done = 0;
        foreach (var line in lines)
        {
            var parts = line.Split(' ');
            byte[] input = Hex(parts[1]), want = Hex(parts[2]);
            var r = Transact(0x71, 0, input, 1000);
            if (r == null) return "no reply at step " + done;
            if (r[3] != 0) return "status " + r[3] + " at step " + done + " (is the test firmware flashed?)";
            for (int i = 0; i < want.Length; i++)
            {
                if (r[4 + i] == want[i]) continue;
                string[] fields = { "logical buttons", "physical inputs", "axes", "hats", "shift", "LEDs", "PWM" };
                int[] starts = { 0, 8, 16, 32, 36, 37, 39 };
                int f = 0;
                while (f + 1 < starts.Length && i >= starts[f + 1]) f++;
                return string.Format("step {0} (t={1}): {2} differ at byte {3}: Pro Micro {4} vs PC {5}",
                    done, BitConverter.ToUInt16(input, 0), fields[f], i,
                    BitConverter.ToString(r, 4, want.Length), BitConverter.ToString(want));
            }
            done++;
        }
        return null;
    }

    public static ushort Crc16(byte[] d, int len)
    {
        ushort crc = 0xFFFF;
        for (int i = 0; i < len; i++)
        {
            crc ^= (ushort)(d[i] << 8);
            for (int b = 0; b < 8; b++) crc = (crc & 0x8000) != 0 ? (ushort)((crc << 1) ^ 0x1021) : (ushort)(crc << 1);
        }
        return crc;
    }

    // Read up to count input reports from a HID interface (e.g. the joystick).
    public static string RawReports(string path, int count, int timeoutMs)
    {
        var sb = new StringBuilder();
        var h = CreateFile(path, 0x80000000, 3, IntPtr.Zero, 3, 0x40000000, IntPtr.Zero);   // read, overlapped
        if (h.IsInvalid) return "can't open the joystick interface (error " + Marshal.GetLastWin32Error() + ")\n";
        using (var f = new FileStream(h, FileAccess.Read, 64, true))
        {
            var b = new byte[64];
            for (int i = 0; i < count; i++)
            {
                var t = f.ReadAsync(b, 0, b.Length);
                if (!t.Wait(timeoutMs)) { sb.Append("timeout: no report\n"); break; }
                int n = t.Result;
                sb.Append(BitConverter.ToString(b, 0, n)).Append("\n");
            }
        }
        return sb.ToString();
    }

    // ---------------------------------------------------- joystick API --

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct JOYCAPSW
    {
        public ushort wMid, wPid;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string szPname;
        public uint wXmin, wXmax, wYmin, wYmax, wZmin, wZmax, wNumButtons, wPeriodMin, wPeriodMax,
            wRmin, wRmax, wUmin, wUmax, wVmin, wVmax, wCaps, wMaxAxes, wNumAxes, wMaxButtons;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string szRegKey;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string szOEMVxD;
    }
    [StructLayout(LayoutKind.Sequential)]
    public struct JOYINFOEX
    {
        public int dwSize, dwFlags, dwXpos, dwYpos, dwZpos, dwRpos, dwUpos, dwVpos, dwButtons, dwButtonNumber, dwPOV, dwReserved1, dwReserved2;
    }
    [DllImport("winmm.dll", CharSet = CharSet.Unicode)] static extern int joyGetDevCapsW(IntPtr id, ref JOYCAPSW c, int size);
    [DllImport("winmm.dll")] static extern int joyGetPosEx(int id, ref JOYINFOEX info);

    public static string Joysticks(ushort vid, ushort pid)
    {
        var sb = new StringBuilder();
        for (int id = 0; id < 16; id++)
        {
            var c = new JOYCAPSW();
            if (joyGetDevCapsW(new IntPtr(id), ref c, Marshal.SizeOf(c)) != 0) continue;
            if (c.wMid != vid || c.wPid != pid) continue;
            var j = new JOYINFOEX(); j.dwSize = Marshal.SizeOf(j); j.dwFlags = 0xFF;   // JOY_RETURNALL
            int r = joyGetPosEx(id, ref j);
            // The first call opens the device and can answer before any report
            // has arrived: wait for a few reports and ask again.
            System.Threading.Thread.Sleep(200);
            j = new JOYINFOEX(); j.dwSize = Marshal.SizeOf(j); j.dwFlags = 0xFF;
            r = joyGetPosEx(id, ref j);
            sb.AppendFormat("joystick id {0}: VID {1:X4} PID {2:X4}, {3} axes, {4} buttons, caps 0x{5:X}\n", id, c.wMid, c.wPid, c.wNumAxes, c.wNumButtons, c.wCaps);
            if (r == 0)
                sb.AppendFormat("  X {0} Y {1} Z {2} R {3} U {4} V {5}  buttons 0x{6:X8}  POV {7}\n", j.dwXpos, j.dwYpos, j.dwZpos, j.dwRpos, j.dwUpos, j.dwVpos, j.dwButtons, j.dwPOV);
            else
                sb.AppendFormat("  joyGetPosEx error {0}\n", r);
        }
        return sb.Length > 0 ? sb.ToString() : "no joystick with that VID/PID in the Windows joystick API\n";
    }
}
'@
}



$CONFIG_SIZE = 652
$CHUNK = 60
$CHUNKS = [int][math]::Ceiling($CONFIG_SIZE / $CHUNK)
$CMD = @{ INFO = 1; READ = 2; WRITE = 3; COMMIT = 4; RELOAD = 5; DEFAULTS = 6; PARAMS = 7; BOOTLOADER = 8 }
$STATUS = @('OK', 'ERR_COMMAND', 'ERR_INDEX', 'ERR_CRC', 'ERR_VERSION', 'ERR_BUSY')

function Get-HsrInterfaces { [Hsr]::List() | Where-Object { $_.Manufacturer -eq 'HeliSR' } }

function Open-Settings {
    $dev = Get-HsrInterfaces | Where-Object { $_.UsagePage -eq 0xFF00 } | Select-Object -First 1
    if (-not $dev) { throw 'No HeliSR settings channel found (is the board plugged in and running HeliSR firmware?)' }
    [Hsr]::Open($dev.Path)
}

function Invoke-Cmd([int]$cmd, [int]$index = 0, [byte[]]$data = $null, [int]$timeout = 1000) {
    $r = [Hsr]::Transact([byte]$cmd, [byte]$index, $data, $timeout)
    if (-not $r) { throw "No reply to command $cmd (index $index)" }
    if ($r[3] -ne 0) { throw "Command $cmd (index $index) failed: $($STATUS[$r[3]])" }
    return $r
}

function Read-Config {
    $cfg = New-Object byte[] $CONFIG_SIZE
    for ($i = 0; $i -lt $CHUNKS; $i++) {
        $r = Invoke-Cmd $CMD.READ $i
        $len = [math]::Min($CHUNK, $CONFIG_SIZE - $i * $CHUNK)
        [Array]::Copy($r, 4, $cfg, $i * $CHUNK, $len)
    }
    return , $cfg
}

function Write-Config([byte[]]$cfg) {
    for ($i = 0; $i -lt $CHUNKS; $i++) {
        $len = [math]::Min($CHUNK, $CONFIG_SIZE - $i * $CHUNK)
        $d = New-Object byte[] $len
        [Array]::Copy($cfg, $i * $CHUNK, $d, 0, $len)
        Invoke-Cmd $CMD.WRITE $i $d | Out-Null
    }
    $crc = [Hsr]::Crc16($cfg, $CONFIG_SIZE)
    Invoke-Cmd $CMD.COMMIT 0 ([byte[]]@(($crc -band 0xFF), ($crc -shr 8))) 5000 | Out-Null
}

function SByte([int]$v) { if ($v -gt 127) { $v - 256 } else { $v } }

function Show-Config([byte[]]$c) {
    $name = [Text.Encoding]::ASCII.GetString($c, 2, 26).TrimEnd([char]0)
    $u16 = { param($o) [BitConverter]::ToUInt16($c, $o) }
    "config_version  $(& $u16 0)"
    "device_name     '$name'"
    "debounce_ms     $(& $u16 28)   encoder_press_ms $($c[30])   exchange_period_ms $($c[31])"
    "spare pins      $(($c[32..42] | ForEach-Object { $_ }) -join ' ')"
    $axes = for ($i = 0; $i -lt 8; $i++) {
        $o = 43 + 30 * $i      # axis_config_t: flags at +6, source_main at +20
        '{0}:{1}{2}' -f $i, (SByte $c[$o + 20]), $(if ($c[$o + 6] -band 1) { '*' } else { '' })
    }
    "axes (output:source, * = enabled)  $($axes -join ' ')"
    $btn = for ($i = 0; $i -lt 64; $i++) { SByte $c[283 + 3 * $i] }
    "buttons 1-20 -> physical  $(($btn[0..19]) -join ' ')"
    $usbVid = & $u16 600; $usbPid = & $u16 602
    "USB IDs         {0:X4}:{1:X4}" -f $usbVid, $usbPid
}

