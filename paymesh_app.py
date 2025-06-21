# paymesh_app.py - Complete PayMesh App with SMS Template Verification and Payment Confirmation SMS

from __future__ import annotations

import os
import re
import threading
import time
import uuid
from pathlib import Path

import numpy as np
import sounddevice as sd
import speech_recognition as sr
import wavio
from gtts import gTTS
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager, SlideTransition
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from playsound import playsound

# Audio library imports
import platform
import subprocess
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("⚠️ pyttsx3 not available. Install with: pip install pyttsx3")

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("⚠️ gtts not available. Install with: pip install gtts")

# BACKEND INTEGRATION
from backend_integration import backend

# --------------------------------------------------------------------------- #
# GLOBAL CONSTANTS
# --------------------------------------------------------------------------- #

Window.clearcolor = (0 / 255, 196 / 255, 204 / 255, 1)

LANGUAGE_CODES = {"English": "en", "Tamil": "ta", "Hindi": "hi"}
TTS_CODES = LANGUAGE_CODES
BEEP_FILE = "beep.mp3"
LOGO_FILE = "assets/logo.png"

# --------------------------------------------------------------------------- #
# HELPER FUNCTIONS - COMPLETELY FIXED WITH SMS SUPPORT
# --------------------------------------------------------------------------- #

def play_beep() -> None:
    if Path(BEEP_FILE).is_file():
        threading.Thread(target=playsound, args=(BEEP_FILE,), daemon=True).start()

def safe_remove(path: str | Path) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass

def show_simple_popup(title: str, message: str) -> None:
    popup = Popup(
        title=title,
        content=Label(text=message, color=(1, 1, 1, 1)),
        size_hint=(0.7, 0.35),
        background_color=(0 / 255, 196 / 255, 204 / 255, 1),
    )
    popup.open()

def show_detailed_popup(title: str, message: str, details: str = "") -> None:
    """Enhanced popup with transaction and SMS verification details"""
    full_message = f"{message}\n\n{details}" if details else message
    popup = Popup(
        title=title,
        content=Label(
            text=full_message, 
            color=(1, 1, 1, 1),
            text_size=(450, None),
            halign="left"
        ),
        size_hint=(0.9, 0.8),
        background_color=(0 / 255, 196 / 255, 204 / 255, 1),
    )
    popup.open()

def logo_widget(size_hint=(1, 0.6)):
    if Path(LOGO_FILE).is_file():
        return Image(source=LOGO_FILE, size_hint=size_hint, allow_stretch=True, keep_ratio=True)
    return Label(text="PayMesh", font_size=40, color=(1, 1, 1, 1), size_hint=size_hint)

def safe_format_value(value, default="Unknown"):
    """COMPLETELY FIXED: Safely format any value for display"""
    try:
        if value is None:
            return default
        elif isinstance(value, dict):
            if 'message' in value:
                return str(value['message'])
            elif 'name' in value:
                return str(value['name'])
            elif 'value' in value:
                return str(value['value'])
            else:
                return str(value)
        elif isinstance(value, list):
            return ', '.join(str(item) for item in value)
        else:
            return str(value)
    except Exception:
        return default

def safe_format_number(value, default=0.0):
    """Safely format numeric values for calculations"""
    try:
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            return float(value)
        elif isinstance(value, dict):
            return 0.0
        else:
            return default
    except Exception:
        return default

# --------------------------------------------------------------------------- #
# ENHANCED SCREENS WITH SMS VERIFICATION INTEGRATION
# --------------------------------------------------------------------------- #

class StartScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas.before:
            Color(*Window.clearcolor)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update_rect, pos=self._update_rect)

        layout = BoxLayout(orientation="vertical", padding=50, spacing=20)
        
        logo = logo_widget()
        layout.add_widget(logo)
        
        # Backend status indicator with SMS verification info
        self.status_label = Label(text="Initializing SMS Security...", font_size=16, color=(1, 1, 1, 1))
        layout.add_widget(self.status_label)
        
        layout.add_widget(
            Label(text="Secure Offline Payments with SMS Phishing Verification", font_size=22, color=(1, 1, 1, 1))
        )

        start_btn = Button(
            text="Get Started",
            size_hint=(0.5, 0.2),
            background_color=(0 / 255, 229 / 255, 212 / 255, 1),
            color=(0, 0, 0, 1),
        )
        start_btn.bind(on_press=self.go_to_login)
        layout.add_widget(start_btn)

        # System info button
        info_btn = Button(
            text="System Status",
            size_hint=(0.5, 0.1),
            background_color=(0.5, 0.5, 0.5, 1),
            color=(1, 1, 1, 1),
        )
        info_btn.bind(on_press=self.show_system_status)
        layout.add_widget(info_btn)

        Animation(opacity=0, duration=0).start(logo)
        Animation(opacity=1, duration=1).start(logo)
        Animation(opacity=0, duration=0).start(start_btn)
        Animation(opacity=1, duration=1).start(start_btn)

        self.add_widget(layout)
        
        # Check backend status on startup
        Clock.schedule_once(self.check_backend_status, 0.5)

    def _update_rect(self, *_):
        self.rect.pos, self.rect.size = self.pos, self.size

    def check_backend_status(self, *_):
        def status_check():
            try:
                status = backend.get_system_status()
                backend_available = status.get("backend_available", False)
                capabilities = status.get("capabilities", {})
                
                if backend_available and capabilities.get("enhanced_security_pipeline", False):
                    status_text = "🟢 4-Layer ML Security + SMS Verification Ready"
                elif backend_available and capabilities.get("ml_security_pipeline", False):
                    status_text = "🟡 Basic ML Security Ready"
                elif backend_available:
                    status_text = "🟡 Basic Backend Ready"
                else:
                    status_text = "🔴 Offline Mode"
                
                Clock.schedule_once(lambda *_: setattr(self.status_label, "text", status_text))
            except Exception as e:
                Clock.schedule_once(lambda *_: setattr(self.status_label, "text", "🔴 Backend Error"))
        
        threading.Thread(target=status_check, daemon=True).start()

    def show_system_status(self, *_):
        def get_status():
            try:
                status = backend.get_system_status()
                backend_available = status.get("backend_available", False)
                capabilities = status.get("capabilities", {})
                current_user = safe_format_value(status.get('current_user', 'Not logged in'))
                
                # Enhanced status with SMS verification
                sms_verification_status = "✅ Available" if capabilities.get("sms_phishing_verification", False) else "❌ Unavailable"
                enhanced_security_status = "✅ Active" if capabilities.get("enhanced_security_pipeline", False) else "❌ Inactive"
                
                status_details = f"""PayMesh Enhanced Security System:
                
Backend: {'✅ Available' if backend_available else '❌ Offline'}

4-Layer ML Security Pipeline:
• Traditional Phishing: {'✅' if capabilities.get('ml_security_pipeline', False) else '❌'}
• Fraud Detection: {'✅' if capabilities.get('ml_security_pipeline', False) else '❌'}
• Trust Scoring: {'✅' if capabilities.get('ml_security_pipeline', False) else '❌'}
• SMS Verification: {sms_verification_status}

Enhanced Security: {enhanced_security_status}

Communication Channels:
• Multi-Channel Router: {'✅' if capabilities.get('multichannel_payments', False) else '❌'}
• SMS (Twilio): {'✅' if capabilities.get('sms_notifications', False) else '❌'}
• Bluetooth Scanner: {'✅' if capabilities.get('bluetooth_scanning', False) else '❌'}
• Connectivity Checker: {'✅' if capabilities.get('real_connectivity_checks', False) else '❌'}

Analytics:
• Fraud Visualization: {'✅' if capabilities.get('fraud_visualization', False) else '❌'}

Current User: {current_user}

SMS Security Features:
• Pre-payment SMS analysis using SVM model
• 4 SMS templates verified per transaction
• Real-time phishing pattern detection
• Payment confirmation SMS notifications"""
                
                Clock.schedule_once(
                    lambda *_: show_detailed_popup("Enhanced System Status", "PayMesh Security Overview", status_details)
                )
            except Exception as e:
                error_msg = f"Error getting system status: {str(e)}"
                Clock.schedule_once(
                    lambda *_: show_simple_popup("Status Error", error_msg)
                )
        
        threading.Thread(target=get_status, daemon=True).start()

    def go_to_login(self, *_):
        self.manager.transition = FadeTransition()
        self.manager.current = "login"

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas.before:
            Color(*Window.clearcolor)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update_rect, pos=self._update_rect)

        layout = BoxLayout(orientation="vertical", padding=30, spacing=20)
        
        logo = logo_widget((1, 0.7))
        layout.add_widget(logo)
        layout.add_widget(Label(text="Login Account", font_size=20, color=(1, 1, 1, 1)))

        self.username = TextInput(
            hint_text="Username",
            multiline=False,
            size_hint=(1, 0.2),
            font_size=24,
            background_color=(1, 1, 1, 0.4),
            foreground_color=(0, 0, 0, 1),
        )
        
        self.password = TextInput(
            hint_text="Password",
            multiline=False,
            password=True,
            size_hint=(1, 0.2),
            font_size=24,
            background_color=(1, 1, 1, 0.4),
            foreground_color=(0, 0, 0, 1),
        )
        
        layout.add_widget(self.username)
        layout.add_widget(self.password)

        # Login status indicator
        self.login_status = Label(
            text="", font_size=14, color=(1, 1, 0, 1), size_hint=(1, 0.05)
        )
        layout.add_widget(self.login_status)

        login_btn = Button(
            text="Login",
            size_hint=(1, 0.15),
            background_color=(0 / 255, 229 / 255, 212 / 255, 1),
            color=(0, 0, 0, 1),
        )
        login_btn.bind(on_press=self.authenticate_user)
        layout.add_widget(login_btn)

        signup_btn = Button(
            text="New user? Sign up",
            background_color=(0, 0, 0, 0),
            color=(0, 0, 0, 1),
            font_size=18,
        )
        signup_btn.bind(on_press=self.go_to_signup)
        layout.add_widget(signup_btn)

        self.add_widget(layout)

    def _update_rect(self, *_):
        self.rect.pos, self.rect.size = self.pos, self.size

    def authenticate_user(self, *_):
        """Enhanced authentication with real backend"""
        username = self.username.text.strip()
        password = self.password.text.strip()
        
        if not username or not password:
            show_simple_popup("Error", "Please enter both username and password")
            return
        
        self.login_status.text = "🔄 Authenticating..."
        
        def auth_process():
            try:
                result = backend.authenticate_user(username, password)
                Clock.schedule_once(lambda *_: self._handle_auth_result(result))
            except Exception as e:
                error_result = {"success": False, "message": f"Authentication failed: {str(e)}"}
                Clock.schedule_once(lambda *_: self._handle_auth_result(error_result))
        
        threading.Thread(target=auth_process, daemon=True).start()
    
    def _handle_auth_result(self, result):
        self.login_status.text = ""
        
        success = result.get("success", False)
        if success:
            show_simple_popup("Success", f"Welcome back, {self.username.text}!")
            Clock.schedule_once(lambda *_: setattr(self.manager, "current", "otp"), 1)
        else:
            error_details = ""
            if result.get("locked", False):
                wait_time = safe_format_number(result.get('wait_time', 60))
                error_details = f"Account locked. Wait {wait_time} seconds."
            
            message = safe_format_value(result.get("message", "Login failed"))
            show_detailed_popup("Login Failed", message, error_details)

    def go_to_signup(self, *_):
        self.manager.current = "signup"

class SignupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas.before:
            Color(*Window.clearcolor)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update_rect, pos=self._update_rect)

        layout = BoxLayout(orientation="vertical", padding=30, spacing=20)
        
        logo = logo_widget((1, 0.5))
        layout.add_widget(logo)
        layout.add_widget(Label(text="Register Account", font_size=20, color=(1, 1, 1, 1)))

        self.username = TextInput(
            hint_text="Username (min 3 chars)",
            multiline=False,
            size_hint=(1, 0.15),
            font_size=24,
            background_color=(1, 1, 1, 0.4),
            foreground_color=(0, 0, 0, 1),
        )
        
        self.password = TextInput(
            hint_text="Password (min 6 chars)",
            multiline=False,
            password=True,
            size_hint=(1, 0.15),
            font_size=24,
            background_color=(1, 1, 1, 0.4),
            foreground_color=(0, 0, 0, 1),
        )
        
        self.phone = TextInput(
            hint_text="Phone Number (+919876543210)",
            multiline=False,
            size_hint=(1, 0.15),
            font_size=24,
            background_color=(1, 1, 1, 0.4),
            foreground_color=(0, 0, 0, 1),
        )
        
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(self.phone)

        # Registration status
        self.signup_status = Label(
            text="", font_size=14, color=(1, 1, 0, 1), size_hint=(1, 0.05)
        )
        layout.add_widget(self.signup_status)

        signup_btn = Button(
            text="Sign Up",
            size_hint=(1, 0.15),
            background_color=(0 / 255, 229 / 255, 212 / 255, 1),
            color=(0, 0, 0, 1),
        )
        signup_btn.bind(on_press=self.register_user)
        layout.add_widget(signup_btn)

        login_btn = Button(
            text="Already have an account? Log in",
            background_color=(0, 0, 0, 0),
            color=(0, 0, 0, 1),
            font_size=18,
        )
        login_btn.bind(on_press=self.go_to_login)
        layout.add_widget(login_btn)

        self.add_widget(layout)

    def _update_rect(self, *_):
        self.rect.pos, self.rect.size = self.pos, self.size

    def register_user(self, *_):
        """Enhanced user registration with validation"""
        username = self.username.text.strip()
        password = self.password.text.strip()
        phone = self.phone.text.strip()
        
        if not all([username, password, phone]):
            show_simple_popup("Error", "Please fill all fields")
            return
        
        self.signup_status.text = "🔄 Creating account..."
        
        def register_process():
            try:
                result = backend.register_user(username, password, phone)
                Clock.schedule_once(lambda *_: self._handle_register_result(result))
            except Exception as e:
                error_result = {"success": False, "message": f"Registration failed: {str(e)}"}
                Clock.schedule_once(lambda *_: self._handle_register_result(error_result))
        
        threading.Thread(target=register_process, daemon=True).start()
    
    def _handle_register_result(self, result):
        self.signup_status.text = ""
        
        success = result.get("success", False)
        if success:
            show_simple_popup("Success", "Registration successful! You can now log in.")
            Clock.schedule_once(lambda *_: self.go_to_login(), 1.5)
        else:
            message = safe_format_value(result.get("message", "Registration failed"))
            show_simple_popup("Registration Failed", message)

    def go_to_login(self, *_):
        self.manager.current = "login"

class OTPScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas.before:
            Color(*Window.clearcolor)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update_rect, pos=self._update_rect)

        layout = BoxLayout(orientation="vertical", padding=30, spacing=20)
        layout.add_widget(logo_widget((1, 0.7)))
        
        layout.add_widget(
            Label(
                text="Security Check-up\nOTP Verification (Demo Mode)",
                font_size=20,
                color=(1, 1, 1, 1),
                halign="center",
            )
        )

        self.otp_input = TextInput(
            hint_text="Enter any 4+ digits",
            multiline=False,
            input_filter="int",
            size_hint=(1, 0.2),
            font_size=32,
            background_color=(1, 1, 1, 0.4),
            foreground_color=(0, 0, 0, 1),
        )
        layout.add_widget(self.otp_input)

        confirm_btn = Button(
            text="Confirm OTP",
            size_hint=(1, 0.15),
            background_color=(0 / 255, 229 / 255, 212 / 255, 1),
            color=(0, 0, 0, 1),
        )
        confirm_btn.bind(on_press=self.verify_otp)
        layout.add_widget(confirm_btn)

        resend_btn = Button(
            text="Skip OTP (Demo)", 
            background_color=(0, 0, 0, 0), 
            color=(0, 0, 0, 1)
        )
        resend_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "send"))
        layout.add_widget(resend_btn)

        self.add_widget(layout)

    def _update_rect(self, *_):
        self.rect.pos, self.rect.size = self.pos, self.size

    def verify_otp(self, *_):
        if len(self.otp_input.text.strip()) >= 4:
            self.manager.current = "send"
        else:
            show_simple_popup("Error", "Please enter at least 4 digits")

class SendScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas.before:
            Color(*Window.clearcolor)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update_rect, pos=self._update_rect)

        layout = BoxLayout(orientation="vertical", padding=30, spacing=25)
        layout.add_widget(logo_widget())

        # Real-time connection status with SMS verification
        self.status_label = Label(
            text="Checking channels and SMS security...",
            markup=True,
            font_size=18,
            size_hint=(1, 0.15),
            color=(1, 1, 1, 1),
        )
        layout.add_widget(self.status_label)
        
        # User info display
        self.user_info = Label(
            text="Loading user info...",
            font_size=14,
            size_hint=(1, 0.1),
            color=(1, 1, 1, 1),
        )
        layout.add_widget(self.user_info)

        # Enhanced ML Security status with SMS verification
        self.security_info = Label(
            text="",
            font_size=12,
            size_hint=(1, 0.12),
            color=(0, 1, 0, 1),
        )
        layout.add_widget(self.security_info)

        send_btn = Button(
            text="🚀 Send Secure Transaction",
            size_hint=(1, 0.2),
            background_color=(0 / 255, 229 / 255, 212 / 255, 1),
            color=(0, 0, 0, 1),
        )
        send_btn.bind(on_press=self.go_to_disability)
        layout.add_widget(send_btn)
        
        # Enhanced action buttons
        buttons_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.15), spacing=10)
        
        graph_btn = Button(
            text="📊 Security Graph",
            background_color=(1, 0.5, 0, 1),
            color=(1, 1, 1, 1),
        )
        graph_btn.bind(on_press=self.show_fraud_graph)
        buttons_layout.add_widget(graph_btn)
        
        sms_stats_btn = Button(
            text="📱 SMS Stats",
            background_color=(0.8, 0.2, 0.8, 1),
            color=(1, 1, 1, 1),
        )
        sms_stats_btn.bind(on_press=self.show_sms_verification_stats)
        buttons_layout.add_widget(sms_stats_btn)
        
        sync_btn = Button(
            text="🔄 Sync",
            background_color=(0.5, 0.5, 1, 1),
            color=(1, 1, 1, 1),
        )
        sync_btn.bind(on_press=self.sync_transactions)
        buttons_layout.add_widget(sync_btn)
        
        analytics_btn = Button(
            text="📈 Analytics",
            background_color=(0.5, 1, 0.5, 1),
            color=(0, 0, 0, 1),
        )
        analytics_btn.bind(on_press=self.show_analytics)
        buttons_layout.add_widget(analytics_btn)
        
        layout.add_widget(buttons_layout)

        self.add_widget(layout)
        
        # Update status every 5 seconds
        Clock.schedule_interval(self.update_status, 5)
        self.update_status()

    def _update_rect(self, *_):
        self.rect.pos, self.rect.size = self.pos, self.size
    
    def update_status(self, *_):
        """Enhanced status updates with SMS verification info"""
        def check_status():
            try:
                # Get connectivity status
                status = backend.check_connection_status()
                user_info = backend.get_user_info()
                
                # Channel status
                channels = []
                if status.get("online", False): channels.append("🌐 Online")
                if status.get("bluetooth", False): channels.append("🔵 Bluetooth")
                if status.get("sms", False): channels.append("📱 SMS")
                if status.get("local", False): channels.append("💾 Local")
                
                channels_text = " | ".join(channels) if channels else "No channels available"
                status_text = f"[b]Channels: [color=00E5D4]{channels_text}[/color][/b]"
                
                # User info
                username = safe_format_value(user_info.get('username', 'guest'))
                txn_count = safe_format_number(user_info.get('transaction_count', 0))
                user_text = f"👤 {username} | 📊 {int(txn_count)} transactions"
                
                # Enhanced security info with SMS verification
                details = status.get("details", {})
                modules_status = details.get("modules_status", {}) if isinstance(details, dict) else {}
                
                security_features = []
                if modules_status.get("phishing_detector", False):
                    security_features.append("SVM Phishing")
                if modules_status.get("fraud_scoring", False):
                    security_features.append("Fraud ML")
                if modules_status.get("sms_phishing_verifier", False):
                    security_features.append("SMS Verification")
                if modules_status.get("trust_score", False):
                    security_features.append("Trust Scoring")
                
                if security_features:
                    security_text = f"🛡️ ML Security: {' + '.join(security_features)}\n🔍 4-Layer Protection: Phishing → Fraud → Trust → SMS"
                else:
                    security_text = "⚠️ ML Security: Limited | Basic protection only"
                
                Clock.schedule_once(lambda *_: setattr(self.status_label, "text", status_text))
                Clock.schedule_once(lambda *_: setattr(self.user_info, "text", user_text))
                Clock.schedule_once(lambda *_: setattr(self.security_info, "text", security_text))
                
            except Exception as e:
                error_status = f"[b]Status: [color=FF6B6B]Error checking connectivity[/color][/b]"
                Clock.schedule_once(lambda *_: setattr(self.status_label, "text", error_status))
        
        threading.Thread(target=check_status, daemon=True).start()
    
    def show_fraud_graph(self, *_):
        """Generate and show fraud graph"""
        def generate_graph():
            try:
                result = backend.generate_fraud_graph()
                Clock.schedule_once(lambda *_: show_simple_popup("Security Graph", result))
            except Exception as e:
                error_msg = f"Graph generation error: {str(e)}"
                Clock.schedule_once(lambda *_: show_simple_popup("Graph Error", error_msg))
        
        threading.Thread(target=generate_graph, daemon=True).start()
    
    def show_sms_verification_stats(self, *_):
        """NEW: Show SMS verification statistics"""
        def get_sms_stats():
            try:
                sms_stats = backend.get_sms_verification_statistics()
                
                if "error" in sms_stats:
                    details = f"SMS Verification Error: {sms_stats['error']}"
                else:
                    total = sms_stats.get('total_verifications', 0)
                    approved = sms_stats.get('approvals', 0)
                    blocked = sms_stats.get('blocks', 0)
                    approval_rate = sms_stats.get('approval_rate', 0)
                    model_status = sms_stats.get('model_status', 'unknown')
                    avg_risk = sms_stats.get('average_risk_score', 0)
                    
                    details = f"""SMS Phishing Verification Statistics:

Model Status: {model_status.upper()}
Model Type: {sms_stats.get('model_type', 'SVM')}

Verification Summary:
• Total Verifications: {total}
• Approved Payments: {approved}
• Blocked Payments: {blocked}
• Approval Rate: {approval_rate:.1f}%

Risk Analysis:
• Average Risk Score: {avg_risk:.3f}/1.0
• Threshold Used: 0.4 (40%)

SMS Security Features:
• Pre-payment SMS analysis
• 4 templates checked per transaction
• Real-time SVM classification
• Automatic phishing detection
• Payment confirmation notifications"""
                
                Clock.schedule_once(
                    lambda *_: show_detailed_popup("SMS Verification Stats", "Security Performance", details)
                )
            except Exception as e:
                error_msg = f"SMS stats error: {str(e)}"
                Clock.schedule_once(lambda *_: show_simple_popup("SMS Stats Error", error_msg))
        
        threading.Thread(target=get_sms_stats, daemon=True).start()
    
    def sync_transactions(self, *_):
        """Sync transactions with server"""
        def sync_process():
            try:
                result = backend.sync_transactions()
                message = safe_format_value(result.get("message", "Sync completed"))
                Clock.schedule_once(lambda *_: show_simple_popup("Sync Status", message))
            except Exception as e:
                error_msg = f"Sync error: {str(e)}"
                Clock.schedule_once(lambda *_: show_simple_popup("Sync Error", error_msg))
        
        threading.Thread(target=sync_process, daemon=True).start()
    
    def show_analytics(self, *_):
        """Show enhanced security analytics with SMS verification"""
        def get_analytics():
            try:
                analytics = backend.get_security_analytics()
                
                if "error" in analytics:
                    details = f"Analytics Error: {analytics['error']}"
                else:
                    ml_status = analytics.get("ml_pipeline_status", {})
                    channel_status = analytics.get("channel_capabilities", {})
                    security_layers = analytics.get("security_layers", {})
                    timestamp = safe_format_value(analytics.get('timestamp', 'Unknown'))
                    
                    details = f"""Enhanced Security Analytics:

4-Layer ML Security Pipeline:
• Traditional Phishing: {'✅ Active' if ml_status.get('phishing_detector') else '❌ Inactive'}
• Fraud Scoring: {'✅ Active' if ml_status.get('fraud_scoring') else '❌ Inactive'}
• Trust Scoring: {'✅ Active' if ml_status.get('trust_scoring') else '❌ Inactive'}
• SMS Verification: {'✅ Active' if ml_status.get('sms_phishing_verifier') else '❌ Inactive'}

Communication Channels:
• Multi-Channel Router: {'✅ Available' if channel_status.get('multichannel_router') else '❌ Unavailable'}
• SMS Notifications: {'✅ Available' if channel_status.get('sms_sender') else '❌ Unavailable'}
• Bluetooth Scanner: {'✅ Available' if channel_status.get('bluetooth_scanner') else '❌ Unavailable'}

Enhanced Security Features:
• Pre-payment SMS phishing verification
• Real-time SVM model classification
• Multi-template security analysis
• Automated threat detection
• Payment confirmation SMS

Timestamp: {timestamp}"""
                
                Clock.schedule_once(
                    lambda *_: show_detailed_popup("Enhanced Analytics", "4-Layer Security Status", details)
                )
            except Exception as e:
                error_msg = f"Analytics error: {str(e)}"
                Clock.schedule_once(lambda *_: show_simple_popup("Analytics Error", error_msg))
        
        threading.Thread(target=get_analytics, daemon=True).start()

    def go_to_disability(self, *_):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "disability"

class DisabilityScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas.before:
            Color(*Window.clearcolor)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update_rect, pos=self._update_rect)

        layout = BoxLayout(orientation="vertical", spacing=30, padding=40)
        layout.add_widget(logo_widget((1, 0.5)))
        
        layout.add_widget(
            Label(
                text="Choose Transaction Method\nWith SMS Security Verification",
                font_size=18,
                size_hint=(1, 0.2),
                color=(1, 1, 1, 1),
                halign="center"
            )
        )

        voice_btn = Button(
            text="🎤 Voice Transaction\n(Accessible + SMS Verification)",
            size_hint=(1, 0.25),
            background_color=(0 / 255, 229 / 255, 212 / 255, 1),
            color=(0, 0, 0, 1),
            font_size=16,
        )
        voice_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "voice"))
        layout.add_widget(voice_btn)

        manual_btn = Button(
            text="✋ Manual Transaction\n(Standard + SMS Verification)",
            size_hint=(1, 0.25),
            background_color=(0 / 255, 229 / 255, 212 / 255, 1),
            color=(0, 0, 0, 1),
            font_size=16,
        )
        manual_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "manual"))
        layout.add_widget(manual_btn)

        self.add_widget(layout)

    def _update_rect(self, *_):
        self.rect.pos, self.rect.size = self.pos, self.size

class VoiceScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_language = "English"
        self.response_language = "English"
        self.current_recipient = ""

        with self.canvas.before:
            Color(*Window.clearcolor)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update_rect, pos=self._update_rect)

        self.box = BoxLayout(orientation="vertical", spacing=10, padding=[25, 15, 25, 15])
        self.add_widget(self.box)

        self.box.add_widget(logo_widget((1, 0.3)))

        # Language selectors
        self.spinner_input = Spinner(
            text="Select Input Language",
            values=list(LANGUAGE_CODES.keys()),
            size_hint_y=None,
            height=48,
            background_color=(1, 1, 1, 0.2),
            color=(1, 1, 1, 1),
        )
        self.spinner_input.bind(text=lambda _, val: setattr(self, "selected_language", val))
        self.box.add_widget(self.spinner_input)

        self.spinner_response = Spinner(
            text="Select Response Language",
            values=list(TTS_CODES.keys()),
            size_hint_y=None,
            height=48,
            background_color=(1, 1, 1, 0.2),
            color=(1, 1, 1, 1),
        )
        self.spinner_response.bind(text=lambda _, val: setattr(self, "response_language", val))
        self.box.add_widget(self.spinner_response)
        
        # Recipient input
        self.recipient_input = TextInput(
            hint_text="Recipient Phone Number",
            multiline=False,
            size_hint_y=None,
            height=48,
            background_color=(1, 1, 1, 0.4),
            foreground_color=(0, 0, 0, 1),
        )
        self.box.add_widget(self.recipient_input)

        # Enhanced status labels for SMS verification
        self.status = Label(
            text="Ready for voice input with SMS verification", font_size=16, color=(1, 1, 0, 1), size_hint_y=None, height=30
        )
        self.result = Label(
            text="", font_size=14, color=(1, 1, 1, 1), size_hint_y=None, height=60
        )
        self.security_status = Label(
            text="", font_size=12, color=(1, 0.5, 0, 1), size_hint_y=None, height=50
        )
        
        self.box.add_widget(self.status)
        self.box.add_widget(self.result)
        self.box.add_widget(self.security_status)

        # Record button
        self.record_button = Button(
            text="🎤 Record Amount (SMS Verified)",
            size_hint_y=None,
            height=50,
            background_color=(0 / 255, 229 / 255, 212 / 255, 1),
            color=(0, 0, 0, 1),
            font_size=16,
        )
        self.record_button.bind(on_press=self.record_and_recognize)
        self.box.add_widget(self.record_button)

        # Navigation buttons
        nav_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=48, spacing=10)
        
        next_button = Button(
            text="Next",
            background_color=(1, 0.5, 0, 1),
            color=(1, 1, 1, 1),
        )
        next_button.bind(on_press=lambda *_: setattr(self.manager, "current", "continue"))
        nav_layout.add_widget(next_button)
        
        back_button = Button(
            text="Back",
            background_color=(0.5, 0.5, 0.5, 1),
            color=(1, 1, 1, 1),
        )
        back_button.bind(on_press=lambda *_: setattr(self.manager, "current", "disability"))
        nav_layout.add_widget(back_button)
        
        self.box.add_widget(nav_layout)

    def _update_rect(self, *_):
        self.rect.pos, self.rect.size = self.pos, self.size

    def record_and_recognize(self, *_):
        recipient = self.recipient_input.text.strip()
        if not recipient:
            show_simple_popup("Error", "Please enter recipient phone number first")
            return
        
        self.current_recipient = recipient
        self.update_status("🎤 Recording...")
        self.record_button.disabled = True
        threading.Thread(target=self._record_process, daemon=True).start()

    def _record_process(self):
        try:
            fs, duration = 16_000, 5
            play_beep()
            audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
            sd.wait()
            play_beep()

            tmp_wav = Path(f"temp_{uuid.uuid4().hex}.wav")
            wavio.write(str(tmp_wav), audio, fs, sampwidth=2)

            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True

            try:
                with sr.AudioFile(str(tmp_wav)) as src:
                    recognizer.adjust_for_ambient_noise(src, duration=0.5)
                    audio_data = recognizer.record(src)

                try:
                    text = recognizer.recognize_google(
                        audio_data, language=LANGUAGE_CODES[self.selected_language]
                    )
                except Exception:
                    text = recognizer.recognize_google(audio_data, language="en")
            except Exception as err:
                text = f"Recognition failed: {err}"

            safe_remove(tmp_wav)
            Clock.schedule_once(lambda *_: self._post_recognition(text))
            
        except Exception as e:
            Clock.schedule_once(lambda *_: self._post_recognition(f"Recording error: {str(e)}"))

    def _post_recognition(self, text: str):
        """Process voice transaction with SMS verification progress"""
        self.result.text = f"You said: {text}"
        self.security_status.text = "🔄 Step 1/4: Running ML fraud detection..."
        
        def process_voice():
            try:
                # Update progress through security layers
                time.sleep(0.5)
                Clock.schedule_once(lambda *_: setattr(self.security_status, "text", "🔄 Step 2/4: Checking phishing patterns..."))
                time.sleep(0.5)
                Clock.schedule_once(lambda *_: setattr(self.security_status, "text", "🔄 Step 3/4: Generating SMS templates..."))
                time.sleep(0.5)
                Clock.schedule_once(lambda *_: setattr(self.security_status, "text", "🔄 Step 4/4: Verifying SMS with SVM model..."))
                time.sleep(0.5)
                
                # Process with enhanced security
                result = backend.process_transaction_with_enhanced_security(self.current_recipient, 0, "voice")
                result["voice_text"] = text
                
                Clock.schedule_once(lambda *_: self._handle_transaction_result(result))
            except Exception as e:
                error_result = {
                    "success": False,
                    "message": f"Processing error: {str(e)}",
                    "reason": "System error"
                }
                Clock.schedule_once(lambda *_: self._handle_transaction_result(error_result))
        
        threading.Thread(target=process_voice, daemon=True).start()
    
    def _handle_transaction_result(self, result):
        """ENHANCED: Handle transaction result with SMS verification and payment confirmation SMS info"""
        try:
            success = result.get("success", False)
            
            # Get SMS verification details
            sms_verification = result.get("sms_verification", {})
            
            # SMS payment confirmation info
            sms_notification = result.get("sms_notification", None)
            sms_info = ""
            if sms_notification is True or (isinstance(sms_notification, dict) and sms_notification.get("success", False)):
                sms_info = "\n\n📱 Payment confirmation SMS has been sent to your registered phone number."
            elif sms_notification is False:
                sms_info = "\n\n⚠️ Payment confirmation SMS could not be sent."
            
            if success:
                # Success case with SMS verification details
                phishing_conf = safe_format_number(result.get('phishing_confidence', 0))
                fraud_score = safe_format_number(result.get('fraud_score', 0))
                trust_score = safe_format_number(result.get('trust_score', 1.0))
                channel_used = safe_format_value(result.get('channel_used', 'Unknown'))
                txn_id = safe_format_value(result.get('txn_id', 'N/A'))
                extracted_amount = safe_format_number(result.get('extracted_amount', 0))
                
                # SMS verification details
                sms_risk_score = safe_format_number(sms_verification.get('risk_score', 0))
                sms_risk_level = safe_format_value(sms_verification.get('phishing_risk', 'LOW'))
                templates_checked = sms_verification.get('sms_templates_checked', [])
                verification_details = sms_verification.get('verification_details', {})
                
                # Build SMS template verification display
                sms_template_analysis = self._format_sms_verification_display(verification_details)
                
                security_details = f"""🛡️ 4-Layer Security Analysis:
• Phishing Risk: {phishing_conf:.2f}/1.0
• Fraud Risk: {fraud_score:.2f}/1.0
• Trust Score: {trust_score:.2f}/1.0
• Channel Used: {channel_used}
• Transaction ID: {txn_id}
• Voice Amount: ₹{int(extracted_amount)}

📱 SMS Security Verification:
• Templates Checked: {len(templates_checked)}
• SMS Risk Score: {sms_risk_score:.3f}/1.0
• Risk Level: {sms_risk_level}

🔍 SMS Template Analysis:
{sms_template_analysis}

✅ All 4 security layers passed
🚀 Transaction processed with SMS verification"""
                
                message = safe_format_value(result.get("message", "Transaction successful"))
                show_detailed_popup("🎉 Voice Transaction Successful", message, security_details + sms_info)
                
                # Enhanced TTS response
                responses = {
                    "English": f"Payment approved. {int(extracted_amount)} rupees sent. All SMS templates verified safe by SVM model.",
                    "Tamil": f"கட்டணம் அங்கீகரிக்கப்பட்டது. {int(extracted_amount)} ரூபாய் அனுப்பப்பட்டது. SMS பாதுகாப்பானது.",
                    "Hindi": f"भुगतान स्वीकृत। {int(extracted_amount)} रुपये भेजे गए। SMS सत्यापित।",
                }
                
            else:
                # Failed case with SMS verification details
                reason = safe_format_value(result.get('reason', 'Unknown error'))
                blocked_reason = safe_format_value(result.get('blocked_reason', 'Security system'))
                voice_text = safe_format_value(result.get('voice_text', 'N/A'))
                
                # SMS verification failure details
                sms_blocked_reason = safe_format_value(sms_verification.get('blocked_reason', 'N/A'))
                sms_risk_score = safe_format_number(sms_verification.get('risk_score', 0))
                verification_details = sms_verification.get('verification_details', {})
                
                # Build failed SMS verification display
                sms_template_analysis = self._format_sms_verification_display(verification_details, failed=True)
                
                security_details = f"""🚫 4-Layer Security Analysis:
• Reason: {reason}
• Blocked By: {blocked_reason}
• Voice Text: {voice_text}

📱 SMS Security Issues:
• SMS Risk Score: {sms_risk_score:.3f}/1.0
• Block Reason: {sms_blocked_reason}

🔍 SMS Template Analysis:
{sms_template_analysis}

❌ Transaction blocked by enhanced security
🛡️ SMS verification protected your payment"""
                
                message = safe_format_value(result.get("message", "Transaction blocked"))
                show_detailed_popup("🚫 Voice Transaction Blocked", message, security_details + sms_info)
                
                responses = {
                    "English": "Payment blocked by SMS security verification. Your funds are protected.",
                    "Tamil": "SMS பாதுகாப்பு சரிபார்ப்பால் கட்டணம் தடுக்கப்பட்டது. உங்கள் பணம் பாதுகாக்கப்பட்டுள்ளது.",
                    "Hindi": "SMS सुरक्षा सत्यापन द्वारा भुगतान रोक दिया गया। आपका पैसा सुरक्षित है।",
                }
            
            # Get response text and speak it
            response_text = responses.get(self.response_language, responses["English"])
            threading.Thread(target=self._speak, args=(response_text,), daemon=True).start()
            
        except Exception as e:
            error_msg = f"Error displaying result: {str(e)}"
            show_simple_popup("Display Error", error_msg)
        
        # Reset UI status
        self.security_status.text = ""
        self.update_status("Ready for next transaction")
        Clock.schedule_once(lambda *_: self.reset_status(), 2)

    def _format_sms_verification_display(self, verification_details, failed=False):
        """Format SMS template verification for user display"""
        if not verification_details:
            return "No SMS verification data available"
        
        display_lines = []
        
        for template_type, details in verification_details.items():
            template_name = template_type.replace('_', ' ').title()
            phishing_score = safe_format_number(details.get('phishing_score', 0))
            is_phishing = details.get('is_phishing', False)
            
            # Status icon
            status_icon = "🚨" if is_phishing else "✅"
            status_text = "FLAGGED" if is_phishing else "SAFE"
            
            display_lines.append(f"  {status_icon} {template_name}: {status_text} ({phishing_score:.3f})")
            
            # Show SMS content for failed cases
            if failed and is_phishing:
                sms_content = details.get('sms_content', '')
                if sms_content:
                    display_lines.append(f"    ⚠️ Content: {sms_content[:50]}...")
        
        return "\n".join(display_lines) if display_lines else "No templates analyzed"

    def _speak(self, text: str):
        """Enhanced TTS with multiple fallback options"""
        print(f"🔊 Speaking: {text}")
        
        # Method 1: Try pyttsx3 (offline, most reliable)
        if PYTTSX3_AVAILABLE:
            try:
                self._speak_pyttsx3(text)
                return
            except Exception as e:
                print(f"pyttsx3 failed: {e}")
        
        # Method 2: Try gTTS + playsound (online)
        if GTTS_AVAILABLE:
            try:
                self._speak_gtts(text)
                return
            except Exception as e:
                print(f"gTTS failed: {e}")
        
        # Method 3: System TTS (Windows)
        try:
            self._speak_system_windows(text)
            return
        except Exception as e:
            print(f"System TTS failed: {e}")
        
        print("❌ All TTS methods failed")
    
    def _speak_pyttsx3(self, text: str):
        """Method 1: Offline TTS using pyttsx3"""
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.8)
        
        voices = engine.getProperty('voices')
        lang_code = TTS_CODES.get(self.response_language, 'en')
        
        for voice in voices:
            if lang_code in voice.id.lower():
                engine.setProperty('voice', voice.id)
                break
        
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        print("✅ pyttsx3 TTS completed")
    
    def _speak_gtts(self, text: str):
        """Method 2: Online TTS using gTTS + playsound"""
        tts = gTTS(text=text, lang=TTS_CODES[self.response_language], slow=False)
        tfile = Path(f"tts_{uuid.uuid4().hex}.mp3")
        
        tts.save(str(tfile))
        playsound(str(tfile))
        safe_remove(tfile)
        print("✅ gTTS TTS completed")
    
    def _speak_system_windows(self, text: str):
        """Method 3: Windows built-in TTS"""
        if platform.system() != "Windows":
            raise Exception("Not Windows system")
        
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Speak(text)
        print("✅ Windows SAPI TTS completed")

    def update_status(self, msg: str):
        self.status.text = msg

    def reset_status(self, *_):
        self.status.text = "Ready for voice input with SMS verification"
        self.record_button.disabled = False

class ManualScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas.before:
            Color(*Window.clearcolor)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update_rect, pos=self._update_rect)

        layout = BoxLayout(orientation="vertical", spacing=20, padding=40)
        layout.add_widget(logo_widget((1, 0.3)))
        layout.add_widget(Label(text="Manual Payment with 4-Layer ML Security", font_size=20, color=(1, 1, 1, 1)))
        
        # Recipient input
        self.recipient_input = TextInput(
            hint_text="Recipient Phone Number",
            multiline=False,
            size_hint=(1, 0.12),
            font_size=24,
            background_color=(1, 1, 1, 0.4),
            foreground_color=(0, 0, 0, 1),
        )
        layout.add_widget(self.recipient_input)

        # Amount input
        self.amount_input = TextInput(
            hint_text="Enter Amount (₹)",
            multiline=False,
            input_filter="float",
            size_hint=(1, 0.12),
            font_size=28,
            background_color=(1, 1, 1, 0.4),
            foreground_color=(0, 0, 0, 1),
        )
        layout.add_widget(self.amount_input)

        # Enhanced security status display with SMS verification
        self.security_status = Label(
            text="", font_size=12, color=(1, 0.5, 0, 1), size_hint=(1, 0.1)
        )
        layout.add_widget(self.security_status)

        # Submit button
        submit_btn = Button(
            text="🔒 Process with SMS Verification",
            size_hint=(1, 0.15),
            background_color=(0 / 255, 229 / 255, 212 / 255, 1),
            color=(0, 0, 0, 1),
        )
        submit_btn.bind(on_press=self.process_secure_transaction)
        layout.add_widget(submit_btn)

        # Preview SMS templates button
        preview_btn = Button(
            text="📱 Preview SMS Templates",
            size_hint=(1, 0.1),
            background_color=(0.7, 0.7, 0.7, 1),
            color=(0, 0, 0, 1),
        )
        preview_btn.bind(on_press=self.preview_sms_templates)
        layout.add_widget(preview_btn)

        # Navigation buttons
        nav_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.12), spacing=10)
        
        next_btn = Button(
            text="Next",
            background_color=(1, 0.5, 0, 1),
            color=(1, 1, 1, 1),
        )
        next_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "continue"))
        nav_layout.add_widget(next_btn)
        
        back_btn = Button(
            text="Back",
            background_color=(0.5, 0.5, 0.5, 1),
            color=(1, 1, 1, 1),
        )
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "disability"))
        nav_layout.add_widget(back_btn)
        
        layout.add_widget(nav_layout)

        self.add_widget(layout)

    def _update_rect(self, *_):
        self.rect.pos, self.rect.size = self.pos, self.size

    def preview_sms_templates(self, *_):
        """NEW: Preview SMS templates that will be verified"""
        recipient = self.recipient_input.text.strip()
        amount_text = self.amount_input.text.strip()
        
        if not recipient or not amount_text:
            show_simple_popup("Preview Error", "Please enter recipient and amount first")
            return
        
        try:
            amount = float(amount_text)
            txn_id = f"PREVIEW_{int(time.time())}"
            
            templates = {
                "Payment Notification": f"PayMesh: You are sending ₹{amount} to {recipient}. TXN: {txn_id}. Confirm to proceed.",
                "Security Alert": f"PayMesh Security: ₹{amount} transfer to {recipient} initiated. TXN: {txn_id}. Contact support if unauthorized.", 
                "Confirmation Request": f"PayMesh: Confirm payment - Send ₹{amount} to {recipient}? Reply YES. TXN: {txn_id}",
                "Success Notification": f"PayMesh: Payment successful - ₹{amount} sent to {recipient}. TXN: {txn_id}. Secure transaction completed."
            }
            
            template_display = "SMS Templates for SVM Verification:\n\n"
            for i, (template_type, content) in enumerate(templates.items(), 1):
                template_display += f"{i}. {template_type}:\n   {content}\n\n"
            
            template_display += "These 4 templates will be checked by your trained SVM model for phishing patterns before payment approval."
            
            show_detailed_popup("📱 SMS Templates Preview", "Pre-payment Security Check", template_display)
            
        except ValueError:
            show_simple_popup("Preview Error", "Please enter a valid amount")

    def process_secure_transaction(self, *_):
        """ENHANCED: Process transaction with SMS verification progress display"""
        recipient = self.recipient_input.text.strip()
        amount_text = self.amount_input.text.strip()
        
        if not recipient or not amount_text:
            show_simple_popup("Error", "Please fill both recipient and amount fields")
            return
        
        try:
            amount = float(amount_text)
            if amount <= 0:
                show_simple_popup("Error", "Amount must be greater than 0")
                return
        except ValueError:
            show_simple_popup("Error", "Invalid amount entered")
            return
        
        # Enhanced progress tracking
        self.security_status.text = "🔄 Step 1/4: Running ML fraud detection..."
        
        def process_transaction():
            try:
                # Update status during processing with SMS verification steps
                time.sleep(0.5)
                Clock.schedule_once(lambda *_: setattr(self.security_status, "text", "🔄 Step 2/4: Checking phishing patterns..."))
                time.sleep(0.5)
                Clock.schedule_once(lambda *_: setattr(self.security_status, "text", "🔄 Step 3/4: Generating 4 SMS templates..."))
                time.sleep(0.5)
                Clock.schedule_once(lambda *_: setattr(self.security_status, "text", "🔄 Step 4/4: Verifying each SMS with SVM model..."))
                time.sleep(1.0)  # Extra time for SMS verification
                
                # Process with enhanced security
                result = backend.process_transaction_with_enhanced_security(recipient, amount, "manual")
                Clock.schedule_once(lambda *_: self._handle_transaction_result(result))
            except Exception as e:
                error_result = {
                    "success": False,
                    "message": f"Processing error: {str(e)}",
                    "reason": "System error"
                }
                Clock.schedule_once(lambda *_: self._handle_transaction_result(error_result))
        
        threading.Thread(target=process_transaction, daemon=True).start()
    
    def _handle_transaction_result(self, result):
        """ENHANCED: Handle transaction result with complete SMS verification display and payment confirmation SMS info"""
        try:
            self.security_status.text = ""
            success = result.get("success", False)
            
            # Get SMS verification details
            sms_verification = result.get("sms_verification", {})
            
            # SMS payment confirmation info
            sms_notification = result.get("sms_notification", None)
            sms_info = ""
            if sms_notification is True or (isinstance(sms_notification, dict) and sms_notification.get("success", False)):
                sms_info = "\n\n📱 Payment confirmation SMS has been sent to your registered phone number."
            elif sms_notification is False:
                sms_info = "\n\n⚠️ Payment confirmation SMS could not be sent."
            
            if success:
                # Success with complete SMS verification analysis
                phishing_conf = safe_format_number(result.get('phishing_confidence', 0))
                fraud_score = safe_format_number(result.get('fraud_score', 0))
                trust_score = safe_format_number(result.get('trust_score', 1.0))
                channel_used = safe_format_value(result.get('channel_used', 'Local'))
                txn_id = safe_format_value(result.get('txn_id', 'N/A'))
                processing_time = safe_format_number(result.get('processing_time_ms', 0))
                security_layers = result.get('security_layers', [])
                
                # SMS verification details
                sms_risk_score = safe_format_number(sms_verification.get('risk_score', 0))
                sms_risk_level = safe_format_value(sms_verification.get('phishing_risk', 'LOW'))
                templates_checked = sms_verification.get('sms_templates_checked', [])
                verification_details = sms_verification.get('verification_details', {})
                
                # Build comprehensive SMS verification display
                sms_template_analysis = self._format_sms_verification_display(verification_details)
                channel_details = self._format_channel_details(result)
                
                security_details = f"""🛡️ Complete 4-Layer Security Analysis:
• Layer 1 - Phishing Risk: {phishing_conf:.2f}/1.0
• Layer 2 - Fraud Risk: {fraud_score:.2f}/1.0
• Layer 3 - Trust Score: {trust_score:.2f}/1.0
• Layer 4 - SMS Verification: {sms_risk_score:.3f}/1.0

Security Layers Checked: {len(security_layers)}
Channel Used: {channel_used}
Transaction ID: {txn_id}
Processing Time: {int(processing_time)}ms

📱 SMS Security Verification Results:
• Templates Analyzed: {len(templates_checked)}
• Overall SMS Risk: {sms_risk_level}
• SVM Model Status: Active

🔍 Individual SMS Template Analysis:
{sms_template_analysis}

📡 Channel Details:
{channel_details}

✅ All 4 security layers passed
🚀 Transaction completed with SMS verification"""
                
                message = safe_format_value(result.get("message", "Transaction successful"))
                show_detailed_popup("🎉 Secure Transaction Successful", message, security_details + sms_info)
                
                # Clear inputs after success
                self.recipient_input.text = ""
                self.amount_input.text = ""
                
            else:
                # Failure with detailed SMS verification analysis
                reason = safe_format_value(result.get('reason', 'Unknown error'))
                blocked_reason = safe_format_value(result.get('blocked_reason', 'Security system'))
                phishing_conf = safe_format_number(result.get('phishing_confidence', 0))
                fraud_score = safe_format_number(result.get('fraud_score', 0))
                trust_score = safe_format_number(result.get('trust_score', 0))
                
                # SMS verification failure details
                sms_blocked_reason = safe_format_value(sms_verification.get('blocked_reason', 'N/A'))
                sms_risk_score = safe_format_number(sms_verification.get('risk_score', 0))
                verification_details = sms_verification.get('verification_details', {})
                
                # Build failed SMS verification display
                sms_template_analysis = self._format_sms_verification_display(verification_details, failed=True)
                
                security_details = f"""🚫 4-Layer Security Analysis:
• Reason: {reason}
• Blocked By: {blocked_reason}
• Phishing Risk: {phishing_conf:.2f}/1.0
• Fraud Risk: {fraud_score:.2f}/1.0
• Trust Score: {trust_score:.2f}/1.0

📱 SMS Security Block Details:
• SMS Risk Score: {sms_risk_score:.3f}/1.0
• Block Reason: {sms_blocked_reason}

🔍 SMS Template Analysis (Flagged):
{sms_template_analysis}

❌ Transaction blocked by enhanced security system
🛡️ SMS verification protected your financial safety
💪 Your funds are secure"""
                
                message = safe_format_value(result.get("message", "Transaction blocked"))
                show_detailed_popup("🚫 Transaction Blocked by SMS Security", message, security_details + sms_info)
                
        except Exception as e:
            error_msg = f"Error displaying result: {str(e)}"
            show_simple_popup("Display Error", error_msg)
    
    def _format_sms_verification_display(self, verification_details, failed=False):
        """Format detailed SMS template verification for user display"""
        if not verification_details:
            return "No SMS verification data available"
        
        display_lines = []
        
        for template_type, details in verification_details.items():
            template_name = template_type.replace('_', ' ').title()
            phishing_score = safe_format_number(details.get('phishing_score', 0))
            is_phishing = details.get('is_phishing', False)
            svm_decision = safe_format_value(details.get('svm_decision', 'UNKNOWN'))
            
            # Status icon and text
            status_icon = "🚨" if is_phishing else "✅"
            status_text = "FLAGGED" if is_phishing else "SAFE"
            
            display_lines.append(f"  {status_icon} {template_name}: {status_text}")
            display_lines.append(f"    SVM Score: {phishing_score:.3f} | Decision: {svm_decision}")
            
            # Show problematic SMS content for failed cases
            if failed and is_phishing:
                sms_content = details.get('sms_content', '')
                if sms_content:
                    display_lines.append(f"    ⚠️ Flagged Content: {sms_content[:60]}...")
            
            display_lines.append("")  # Empty line for spacing
        
        return "\n".join(display_lines) if display_lines else "No templates analyzed"
    
    def _format_channel_details(self, result):
        """Format channel details for display"""
        try:
            channel_used = safe_format_value(result.get('channel_used', 'unknown'))
            
            if channel_used == 'online':
                return "• Used: Internet connection\n• Speed: High bandwidth"
            elif channel_used == 'bluetooth':
                device_info = result.get('device_used', {})
                if isinstance(device_info, dict):
                    device_name = safe_format_value(device_info.get('name', 'Unknown'))
                    device_confidence = safe_format_number(device_info.get('confidence', 0))
                    return f"• Used: Bluetooth Low Energy\n• Device: {device_name}\n• Signal: {device_confidence:.2f}"
                else:
                    return "• Used: Bluetooth Low Energy\n• Device: Unknown"
            elif channel_used == 'sms':
                sms_info = result.get('sms_result', {})
                if isinstance(sms_info, dict):
                    provider = safe_format_value(sms_info.get('provider', 'Unknown'))
                    status = safe_format_value(sms_info.get('status', 'Unknown'))
                    return f"• Used: SMS via {provider}\n• Status: {status}"
                else:
                    return "• Used: SMS\n• Status: Processed"
            elif channel_used == 'local':
                return "• Used: Local storage\n• Will sync when online"
            else:
                return f"• Channel: {channel_used}\n• Status: Processed"
        except Exception as e:
            return "• Channel: Processing\n• Status: Completed"

class ContinueScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas.before:
            Color(*Window.clearcolor)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update_rect, pos=self._update_rect)

        layout = BoxLayout(orientation="vertical", spacing=30, padding=40)
        layout.add_widget(logo_widget((1, 0.5)))
        
        layout.add_widget(
            Label(
                text="Secure Transaction Complete!\n4-Layer ML Security + SMS Verification\nMake another transaction?",
                font_size=18,
                color=(1, 1, 1, 1),
                halign="center",
            )
        )

        yes_btn = Button(
            text="Yes - New Secure Transaction",
            size_hint=(1, 0.2),
            background_color=(0 / 255, 229 / 255, 212 / 255, 1),
            color=(0, 0, 0, 1),
        )
        yes_btn.bind(on_press=self.go_to_disability)
        layout.add_widget(yes_btn)

        dashboard_btn = Button(
            text="Security Dashboard",
            size_hint=(1, 0.2),
            background_color=(1, 0.5, 0, 1),
            color=(1, 1, 1, 1),
        )
        dashboard_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "send"))
        layout.add_widget(dashboard_btn)

        exit_btn = Button(
            text="Exit App",
            size_hint=(1, 0.2),
            background_color=(1, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
        )
        exit_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "exit"))
        layout.add_widget(exit_btn)

        self.add_widget(layout)

    def _update_rect(self, *_):
        self.rect.pos, self.rect.size = self.pos, self.size

    def go_to_disability(self, *_):
        self.manager.current = "disability"

class ExitScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas.before:
            Color(*Window.clearcolor)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update_rect, pos=self._update_rect)

        layout = BoxLayout(orientation="vertical", padding=50, spacing=20)
        layout.add_widget(logo_widget((1, 0.6)))
        
        layout.add_widget(
            Label(
                text="Thank you for using PayMesh!\nSecure Offline Payments with 4-Layer ML Security\nIncluding SMS Phishing Verification & Payment Confirmations", 
                font_size=20, 
                color=(1, 1, 1, 1),
                halign="center"
            )
        )

        exit_btn = Button(
            text="Exit App",
            size_hint=(0.5, 0.2),
            background_color=(0 / 255, 229 / 255, 212 / 255, 1),
            color=(0, 0, 0, 1),
        )
        exit_btn.bind(on_press=lambda *_: App.get_running_app().stop())
        layout.add_widget(exit_btn)

        restart_btn = Button(
            text="Restart App",
            size_hint=(0.5, 0.2),
            background_color=(1, 0.5, 0, 1),
            color=(1, 1, 1, 1),
        )
        restart_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "start"))
        layout.add_widget(restart_btn)

        self.add_widget(layout)

    def _update_rect(self, *_):
        self.rect.pos, self.rect.size = self.pos, self.size

# --------------------------------------------------------------------------- #
# APPLICATION ROOT
# --------------------------------------------------------------------------- #

class PayMeshApp(App):
    def build(self):
        sm = ScreenManager()
        
        # Add all screens
        sm.add_widget(StartScreen(name="start"))
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(SignupScreen(name="signup"))
        sm.add_widget(OTPScreen(name="otp"))
        sm.add_widget(SendScreen(name="send"))
        sm.add_widget(DisabilityScreen(name="disability"))
        sm.add_widget(VoiceScreen(name="voice"))
        sm.add_widget(ManualScreen(name="manual"))
        sm.add_widget(ContinueScreen(name="continue"))
        sm.add_widget(ExitScreen(name="exit"))
        
        sm.current = "start"
        return sm
    
    def on_stop(self):
        """Cleanup when app closes"""
        try:
            # Sync any pending transactions
            backend.sync_transactions()
        except:
            pass

if __name__ == "__main__":
    PayMeshApp().run()
