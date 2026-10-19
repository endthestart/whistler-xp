/*
 * Whistler test program. Run as "setup" it installs itself into Program Files
 * and creates Start menu + desktop shortcuts (exercising Wine's menu
 * integration); run from Program Files it shows a window of classic controls.
 *   x86_64-w64-mingw32-gcc -municode -mwindows hello.c -o setup.exe -lole32 -luuid -lcomctl32 -lshell32
 */
#define COBJMACROS
#include <windows.h>
#include <commctrl.h>
#include <objbase.h>
#include <shlobj.h>
#include <shobjidl.h>
#include <wchar.h>

static HRESULT make_link(const wchar_t *target, const wchar_t *link, const wchar_t *desc)
{
    IShellLinkW *sl;
    IPersistFile *pf;
    HRESULT hr = CoCreateInstance(&CLSID_ShellLink, NULL, CLSCTX_INPROC_SERVER, &IID_IShellLinkW, (void **)&sl);
    if (FAILED(hr))
        return hr;
    IShellLinkW_SetPath(sl, target);
    IShellLinkW_SetDescription(sl, desc);
    IShellLinkW_SetIconLocation(sl, target, 0);
    hr = IShellLinkW_QueryInterface(sl, &IID_IPersistFile, (void **)&pf);
    if (SUCCEEDED(hr)) {
        hr = IPersistFile_Save(pf, link, TRUE);
        IPersistFile_Release(pf);
    }
    IShellLinkW_Release(sl);
    return hr;
}

static int install(void)
{
    wchar_t self[MAX_PATH], pf[MAX_PATH], dir[MAX_PATH], exe[MAX_PATH], progs[MAX_PATH], desk[MAX_PATH], buf[MAX_PATH];
    if (MessageBoxW(NULL, L"Install Whistler Hello on this computer?", L"Whistler Hello Setup",
                    MB_YESNO | MB_ICONQUESTION) != IDYES)
        return 1;
    GetModuleFileNameW(NULL, self, MAX_PATH);
    SHGetFolderPathW(NULL, CSIDL_PROGRAM_FILES, NULL, 0, pf);
    swprintf(dir, MAX_PATH, L"%ls\\Whistler Hello", pf);
    CreateDirectoryW(dir, NULL);
    swprintf(exe, MAX_PATH, L"%ls\\hello.exe", dir);
    if (!CopyFileW(self, exe, FALSE)) {
        MessageBoxW(NULL, L"Could not copy files.", L"Whistler Hello Setup", MB_ICONERROR);
        return 2;
    }
    CoInitialize(NULL);
    SHGetFolderPathW(NULL, CSIDL_PROGRAMS, NULL, 0, progs);
    swprintf(buf, MAX_PATH, L"%ls\\Whistler Hello", progs);
    CreateDirectoryW(buf, NULL);
    swprintf(buf, MAX_PATH, L"%ls\\Whistler Hello\\Whistler Hello.lnk", progs);
    make_link(exe, buf, L"A small Windows test program");
    SHGetFolderPathW(NULL, CSIDL_DESKTOPDIRECTORY, NULL, 0, desk);
    swprintf(buf, MAX_PATH, L"%ls\\Whistler Hello.lnk", desk);
    make_link(exe, buf, L"A small Windows test program");
    CoUninitialize();
    MessageBoxW(NULL, L"Whistler Hello was installed.\nYou will find it in Start > All Programs.",
                L"Whistler Hello Setup", MB_ICONINFORMATION);
    return 0;
}

static LRESULT CALLBACK wndproc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp)
{
    switch (msg) {
    case WM_COMMAND:
        if (LOWORD(wp) == 1)
            MessageBoxW(hwnd, L"Hello from a Windows program running on Whistler XP!", L"Hello", MB_ICONINFORMATION);
        else if (LOWORD(wp) == 2)
            DestroyWindow(hwnd);
        return 0;
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(hwnd, msg, wp, lp);
}

static int run_app(HINSTANCE inst)
{
    INITCOMMONCONTROLSEX icc = { sizeof(icc), ICC_PROGRESS_CLASS | ICC_STANDARD_CLASSES };
    WNDCLASSW wc = { 0 };
    HWND hwnd, prog;
    HFONT font = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
    MSG m;
    InitCommonControlsEx(&icc);
    wc.lpfnWndProc = wndproc;
    wc.hInstance = inst;
    wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
    wc.lpszClassName = L"WhistlerHello";
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hIcon = LoadIcon(NULL, IDI_APPLICATION);
    RegisterClassW(&wc);
    hwnd = CreateWindowW(L"WhistlerHello", L"Whistler Hello", WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT,
                         380, 260, NULL, NULL, inst, NULL);
#define CTL(cls, text, style, x, y, w, h, id) \
    SendMessageW(CreateWindowW(cls, text, WS_CHILD | WS_VISIBLE | (style), x, y, w, h, hwnd, (HMENU)(id), inst, NULL), \
                 WM_SETFONT, (WPARAM)font, TRUE)
    CTL(L"STATIC", L"This is a Windows program running through Wine.", 0, 16, 14, 340, 18, 0);
    CTL(L"EDIT", L"Type here", WS_BORDER, 16, 40, 220, 22, 0);
    CTL(L"BUTTON", L"Remember me", BS_AUTOCHECKBOX, 16, 72, 160, 20, 0);
    CTL(L"BUTTON", L"Option A", BS_AUTORADIOBUTTON, 16, 96, 120, 20, 0);
    CTL(L"BUTTON", L"Option B", BS_AUTORADIOBUTTON, 140, 96, 120, 20, 0);
    prog = CreateWindowW(PROGRESS_CLASSW, NULL, WS_CHILD | WS_VISIBLE, 16, 128, 330, 18, hwnd, NULL, inst, NULL);
    SendMessageW(prog, PBM_SETPOS, 60, 0);
    CTL(L"BUTTON", L"Say Hello", BS_DEFPUSHBUTTON, 176, 180, 80, 26, 1);
    CTL(L"BUTTON", L"Close", 0, 266, 180, 80, 26, 2);
    ShowWindow(hwnd, SW_SHOW);
    while (GetMessageW(&m, NULL, 0, 0) > 0) {
        TranslateMessage(&m);
        DispatchMessageW(&m);
    }
    return 0;
}

int WINAPI wWinMain(HINSTANCE inst, HINSTANCE prev, LPWSTR cmd, int show)
{
    wchar_t self[MAX_PATH];
    GetModuleFileNameW(NULL, self, MAX_PATH);
    if (wcsstr(self, L"Program Files") == NULL)
        return install();
    return run_app(inst);
}
