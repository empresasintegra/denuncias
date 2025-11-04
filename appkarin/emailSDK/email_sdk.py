#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import sys
import json
import requests
from azure.identity import ClientSecretCredential

load_dotenv()
# Correo desde el cual ENVIAR (debe tener buzón de Exchange)
# ==========================
class EmailSDK:

    def __init__(self, to, subject, message, sender, cc=None):
        """
        Inicializa EmailSDK
        
        Args:
            to: string o lista de emails destinatarios principales
            subject: asunto del email
            message: contenido HTML del mensaje
            sender: email del remitente
            cc: string o lista de emails en copia (opcional)
        """
        self.sender = sender
        
        # Convertir 'to' a lista si es string
        self.to = [to] if isinstance(to, str) else to
        
        # Convertir 'cc' a lista si es string, o lista vacía si es None
        if cc is None:
            self.cc = []
        elif isinstance(cc, str):
            self.cc = [cc]
        else:
            self.cc = cc
            
        self.subject = subject
        self.message = message
        self.graph = "https://graph.microsoft.com/v1.0"
        self.tenant_id = os.getenv('TENANT_ID')
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET_ID')
        self.token = self.get_token()

    def get_token(self):
        cred = ClientSecretCredential(tenant_id=self.tenant_id, client_id=self.client_id, client_secret=self.client_secret)
        token = cred.get_token("https://graph.microsoft.com/.default").token
        return token

    def graph_request(self, method, url, **kwargs):
        headers = kwargs.pop("headers", {})
        headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)
        return resp

    def mailbox_exists(self):
        """
        Chequeo rápido que NO requiere Directory perms:
        Usa Mail.ReadBasic.All (que ya tienes) para tocar Inbox.
        """
        url = f"{self.graph}/users/{self.sender}/mailFolders/inbox?$top=1"
        r = self.graph_request("GET", url)
        if r.status_code == 200:
            return True, None
        try:
            err = r.json()
        except Exception:
            err = {"raw": r.text}
        return False, {"status": r.status_code, "error": err}

    def send_mail(self, save_to_sent=True):
        url = f"{self.graph}/users/{self.sender}/sendMail"
        
        # Construir lista de destinatarios TO
        to_recipients = [{"emailAddress": {"address": email}} for email in self.to]
        
        # Construir el payload base
        payload = {
            "message": {
                "subject": self.subject,
                "body": {"contentType": "HTML", "content": self.message},
                "toRecipients": to_recipients,
            },
            "saveToSentItems": bool(save_to_sent)
        }
        
        # Agregar CC si hay destinatarios en copia
        if self.cc:
            cc_recipients = [{"emailAddress": {"address": email}} for email in self.cc]
            payload["message"]["ccRecipients"] = cc_recipients
        
        r = self.graph_request("POST", url, data=json.dumps(payload))
        return r

def main():
    # Ejemplo de uso con CC
    email = EmailSDK(
        to="estebanriso2000@gmail.com",
        subject="Prueba con CC",
        message="<h1>Hola mundo!</h1><p>Este email incluye destinatarios en copia.</p>",
        sender="soporte@empresasintegra.onmicrosoft.com",
        cc=["copia1@ejemplo.com", "copia2@ejemplo.com"]  # Puedes pasar una lista
    )
    
    # También puedes pasar un solo email como string
    # cc="copia@ejemplo.com"
    
    # O no pasar CC para no incluir copias
    # email = EmailSDK(to="...", subject="...", message="...", sender="...")

    print("✅ Token OK")

    print(f"📫 Verificando buzón para: {email.sender} …")
    ok, info = email.mailbox_exists()
    if not ok:
        print("❌ El buzón no responde como esperado.")
        print("   Detalle:", json.dumps(info, indent=2))

    print(f"📤 Enviando email desde {email.sender}")
    print(f"   TO: {', '.join(email.to)}")
    if email.cc:
        print(f"   CC: {', '.join(email.cc)}")
    
    resp = email.send_mail()
    if resp.status_code == 202:
        print("🎉 ¡Envío aceptado por Graph! (202)")
        sys.exit(0)

    # Manejo de errores útil
    try:
        err = resp.json()
    except Exception:
        err = {"raw": resp.text}

    print(f"❌ Error al enviar. HTTP {resp.status_code}")
    print(json.dumps(err, indent=2))

    # Diagnóstico rápido según código:
    if resp.status_code == 403:
        print("\n🧭 Pistas:")
        print(" - Si el error menciona 'Authorization_RequestDenied' o 'AccessDenied':")
        print("   > Revisa si hay Application Access Policies en Exchange que restrinjan tu app.")
        print("   > PowerShell (admin):")
        print("     Connect-ExchangeOnline")
        print(f"     Test-ApplicationAccessPolicy -AppId {email.client_id} -Identity {email.sender}")
        print("   > Si da Denied, el admin debe crear/ajustar la policy para permitirte.")
    elif resp.status_code == 404:
        print("\n🧭 Pistas:")
        print(" - Posible 'MailboxNotEnabledForRESTAPI' → Asignar licencia/crear buzón de Exchange.")
    elif resp.status_code in (401, 400):
        print("\n🧭 Pistas:")
        print(" - Revisa credenciales de app, consentimiento de permisos y audiencia '.default'.")

    sys.exit(2)

if __name__ == "__main__":
    main()