// J.A.R.V.I.S. - Desktop Application
// Powered by Tauri v2

#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::process::{Command, Child};
use std::sync::Mutex;
#[cfg(windows)]
use std::os::windows::process::CommandExt;
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager, State,
};

// Estado global para o processo do backend
struct BackendProcess(Mutex<Option<Child>>);

fn is_backend_running() -> bool {
    // Verifica se a porta 8765 está em uso (backend já rodando)
    std::net::TcpStream::connect("127.0.0.1:8765").is_ok()
}

fn start_backend() -> Option<Child> {
    // Se backend já está rodando, não inicia outro
    if is_backend_running() {
        println!("✅ Backend já está rodando!");
        return None;
    }
    
    let backend_path = r"C:\Users\lucas\Downloads\jarvis\backend\main.py";
    
    println!("📁 Iniciando backend: {}", backend_path);
    
    // Iniciar Python completamente em background (sem janela)
    Command::new("pythonw")  // pythonw não abre janela
        .arg(backend_path)
        .creation_flags(0x08000000) // CREATE_NO_WINDOW
        .spawn()
        .or_else(|_| {
            // Fallback para python normal se pythonw não existir
            Command::new("python")
                .arg(backend_path)
                .creation_flags(0x08000000)
                .spawn()
        })
        .ok()
}

fn stop_backend(state: &State<BackendProcess>) {
    if let Ok(mut guard) = state.0.lock() {
        if let Some(mut child) = guard.take() {
            let _ = child.kill();
        }
    }
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            // Verificar se backend já está rodando, senão inicia
            if is_backend_running() {
                println!("✅ Backend já está rodando!");
            } else {
                println!("🚀 Iniciando backend JARVIS...");
                let _backend = start_backend();
                println!("✅ Backend iniciado!");
            }
            
            // Criar menu da bandeja
            let quit = MenuItem::with_id(app, "quit", "Sair", true, None::<&str>)?;
            let show = MenuItem::with_id(app, "show", "Mostrar", true, None::<&str>)?;
            let hide = MenuItem::with_id(app, "hide", "Ocultar", true, None::<&str>)?;
            
            let menu = Menu::with_items(app, &[&show, &hide, &quit])?;
            
            let _tray = TrayIconBuilder::new()
                .menu(&menu)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "quit" => {
                        // Parar backend antes de sair
                        let state: State<BackendProcess> = app.state();
                        stop_backend(&state);
                        app.exit(0);
                    }
                    "show" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    "hide" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.hide();
                        }
                    }
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(app)?;
            
            Ok(())
        })
        .on_window_event(|window, event| {
            // Parar backend quando fechar a janela principal
            if let tauri::WindowEvent::Destroyed = event {
                let state: State<BackendProcess> = window.state();
                stop_backend(&state);
            }
        })
        .run(tauri::generate_context!())
        .expect("Erro ao executar aplicação Tauri");
}
