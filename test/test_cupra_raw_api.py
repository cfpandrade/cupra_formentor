#!/usr/bin/env python3
"""
Test directo de la API de Cupra usando requests
Para diagnosticar problemas de conectividad básica
Sin dependencias externas - solo usa la librería requests estándar
"""

import sys
try:
    import requests
except ImportError:
    print("❌ requests no está instalado. Instala con: pip install requests")
    sys.exit(1)
import json
import getpass
from urllib.parse import parse_qs, urlparse

class CupraAPITest:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # URLs base de Cupra
        self.base_url = "https://cupraid.vwgroup.io"
        self.api_url = "https://mobileapi.apps.emea.vwapps.io"
        
    def test_connectivity(self):
        """Probar conectividad básica"""
        print("🌐 Probando conectividad...")
        
        try:
            response = self.session.get(f"{self.base_url}/portal", timeout=10)
            print(f"✅ Conectividad OK - Status: {response.status_code}")
            return True
        except Exception as e:
            print(f"❌ Error de conectividad: {e}")
            return False
    
    def test_login_page(self):
        """Probar acceso a la página de login"""
        print("🔐 Probando página de login...")
        
        try:
            # Intentar acceder a la página de login
            login_url = f"{self.base_url}/portal/login"
            response = self.session.get(login_url, timeout=10)
            
            if response.status_code == 200:
                print("✅ Página de login accesible")
                
                # Buscar formularios o APIs en la respuesta
                if "vwgroup" in response.text.lower():
                    print("✅ Detectado portal VW Group")
                
                return True
            else:
                print(f"⚠️  Página de login - Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error accediendo a login: {e}")
            return False
    
    def test_identity_provider(self):
        """Probar el proveedor de identidad"""
        print("🆔 Probando proveedor de identidad...")
        
        try:
            # URL del proveedor de identidad
            identity_url = "https://identity.vwgroup.io"
            response = self.session.get(f"{identity_url}/oidc/v1/authorize", 
                                      timeout=10, 
                                      allow_redirects=False)
            
            if response.status_code in [200, 302, 400]:  # 400 es normal sin parámetros
                print(f"✅ Proveedor de identidad accesible - Status: {response.status_code}")
                return True
            else:
                print(f"⚠️  Proveedor de identidad - Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error con proveedor de identidad: {e}")
            return False
    
    def test_mobile_api(self):
        """Probar API móvil"""
        print("📱 Probando API móvil...")
        
        try:
            # Probar endpoint de la API móvil
            response = self.session.get(f"{self.api_url}/health", timeout=10)
            
            if response.status_code in [200, 404]:  # 404 es normal si no existe /health
                print(f"✅ API móvil accesible - Status: {response.status_code}")
                return True
            else:
                print(f"⚠️  API móvil - Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error con API móvil: {e}")
            return False
    
    def attempt_basic_auth(self, email, password):
        """Intentar autenticación básica"""
        print("🔑 Intentando autenticación básica...")
        
        try:
            # Datos de login
            login_data = {
                "email": email,
                "password": password
            }
            
            # Intentar login en diferentes endpoints
            endpoints = [
                f"{self.base_url}/portal/api/auth/login",
                f"{self.base_url}/api/auth/login",
                f"{self.api_url}/auth/login"
            ]
            
            for endpoint in endpoints:
                try:
                    print(f"   Probando: {endpoint}")
                    response = self.session.post(endpoint, 
                                               json=login_data, 
                                               timeout=10)
                    
                    print(f"   Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        print("   ✅ Login exitoso!")
                        print(f"   Response: {response.text[:200]}...")
                        return True
                    elif response.status_code == 401:
                        print("   ❌ Credenciales incorrectas")
                    elif response.status_code == 404:
                        print("   ℹ️  Endpoint no encontrado")
                    else:
                        print(f"   ⚠️  Status: {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Error: {e}")
            
            return False
            
        except Exception as e:
            print(f"❌ Error en autenticación: {e}")
            return False
    
    def check_network_requirements(self):
        """Verificar requisitos de red"""
        print("🔍 Verificando requisitos de red...")
        
        # Dominios importantes de Cupra/VW
        domains = [
            "cupraid.vwgroup.io",
            "identity.vwgroup.io", 
            "mobileapi.apps.emea.vwapps.io",
            "msg.volkswagen.de",
            "carnet.volkswagen.de"
        ]
        
        for domain in domains:
            try:
                response = self.session.get(f"https://{domain}", 
                                          timeout=5, 
                                          allow_redirects=False)
                status = "✅" if response.status_code < 400 else "⚠️"
                print(f"   {status} {domain} - Status: {response.status_code}")
                
            except Exception as e:
                print(f"   ❌ {domain} - Error: {e}")
    
    def run_full_test(self):
        """Ejecutar test completo"""
        print("🔧 Test de API Cupra - Diagnóstico completo")
        print("=" * 50)
        
        # Tests básicos
        tests = [
            self.test_connectivity,
            self.test_login_page,
            self.test_identity_provider,
            self.test_mobile_api,
            self.check_network_requirements
        ]
        
        for test in tests:
            try:
                test()
                print()
            except Exception as e:
                print(f"❌ Error en {test.__name__}: {e}\n")
        
        # Test de autenticación
        print("🔐 Test de autenticación:")
        email = input("Email (opcional, presiona Enter para saltar): ").strip()
        
        if email:
            password = getpass.getpass("Password: ")
            self.attempt_basic_auth(email, password)
        else:
            print("⏭️  Saltando test de autenticación")
        
        print("\n✅ Diagnóstico completado!")

def main():
    """Función principal"""
    tester = CupraAPITest()
    tester.run_full_test()

if __name__ == "__main__":
    main()
