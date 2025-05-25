#!/usr/bin/env python3
"""
Script de prueba para la API de Cupra WeConnect
Basado en WeConnect-Cupra-python
"""

import asyncio
import logging
import sys
from datetime import datetime

# Configurar logging para ver detalles
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_cupra_api():
    """Función principal para probar la API de Cupra"""
    
    try:
        # Importar la librería WeConnect-Cupra
        from weconnect_cupra import WeConnect
        from weconnect_cupra.domain import Domain
        
        print("✅ Librería WeConnect-Cupra importada correctamente")
        
    except ImportError as e:
        print(f"❌ Error importando WeConnect-Cupra: {e}")
        print("📦 Instala la librería con: pip install weconnect-cupra")
        return False
    
    # Solicitar credenciales
    print("\n🔐 Configuración de credenciales:")
    email = input("Email de Cupra WeConnect: ").strip()
    password = input("Password: ").strip()
    
    if not email or not password:
        print("❌ Email y password son requeridos")
        return False
    
    print(f"\n🚀 Iniciando conexión con {email}...")
    
    try:
        # Crear instancia de WeConnect
        weconnect = WeConnect(
            username=email,
            password=password,
            updateAfterLogin=False,
            loginOnInit=False
        )
        
        print("✅ Instancia WeConnect creada")
        
        # Intentar login
        print("🔑 Intentando login...")
        await weconnect.login()
        print("✅ Login exitoso!")
        
        # Actualizar datos
        print("📡 Obteniendo datos de vehículos...")
        await weconnect.update()
        print("✅ Datos actualizados")
        
        # Listar vehículos
        vehicles = weconnect.vehicles
        print(f"\n🚗 Vehículos encontrados: {len(vehicles)}")
        
        if not vehicles:
            print("⚠️  No se encontraron vehículos en la cuenta")
            return True
        
        # Iterar por cada vehículo
        for vin, vehicle in vehicles.items():
            print(f"\n{'='*50}")
            print(f"🚙 VIN: {vin}")
            print(f"📛 Modelo: {vehicle.model}")
            print(f"🏷️  Nickname: {getattr(vehicle, 'nickname', 'N/A')}")
            
            # Información básica del vehículo
            print(f"\n📊 Información básica:")
            if hasattr(vehicle, 'domains'):
                for domain_name, domain in vehicle.domains.items():
                    print(f"   {domain_name}: {domain}")
            
            # Estado de carga (si es eléctrico/híbrido)
            print(f"\n🔋 Estado de carga:")
            try:
                if hasattr(vehicle, 'domains') and Domain.CHARGING in vehicle.domains:
                    charging = vehicle.domains[Domain.CHARGING]
                    
                    if hasattr(charging, 'chargingStatus'):
                        status = charging.chargingStatus
                        print(f"   Estado: {status.chargingState.value if hasattr(status, 'chargingState') else 'N/A'}")
                        print(f"   Potencia: {status.chargePower_kW.value if hasattr(status, 'chargePower_kW') and status.chargePower_kW else 'N/A'} kW")
                        print(f"   Velocidad: {status.chargeRate_kmph.value if hasattr(status, 'chargeRate_kmph') and status.chargeRate_kmph else 'N/A'} km/h")
                        print(f"   Tiempo restante: {status.remainingChargingTimeToComplete_min.value if hasattr(status, 'remainingChargingTimeToComplete_min') and status.remainingChargingTimeToComplete_min else 'N/A'} min")
                
                else:
                    print("   ⚠️  Sin información de carga (vehículo no eléctrico/híbrido)")
                    
            except Exception as e:
                print(f"   ❌ Error obteniendo estado de carga: {e}")
            
            # Batería
            print(f"\n🔋 Batería:")
            try:
                if hasattr(vehicle, 'domains') and Domain.CHARGING in vehicle.domains:
                    charging = vehicle.domains[Domain.CHARGING]
                    
                    if hasattr(charging, 'batteryStatus'):
                        battery = charging.batteryStatus
                        print(f"   Nivel: {battery.currentSOC_pct.value if hasattr(battery, 'currentSOC_pct') and battery.currentSOC_pct else 'N/A'}%")
                        print(f"   Autonomía: {battery.cruisingRangeElectric_km.value if hasattr(battery, 'cruisingRangeElectric_km') and battery.cruisingRangeElectric_km else 'N/A'} km")
                
                else:
                    print("   ⚠️  Sin información de batería")
                    
            except Exception as e:
                print(f"   ❌ Error obteniendo estado de batería: {e}")
            
            # Ubicación
            print(f"\n📍 Ubicación:")
            try:
                if hasattr(vehicle, 'domains') and Domain.PARKING in vehicle.domains:
                    parking = vehicle.domains[Domain.PARKING]
                    
                    if hasattr(parking, 'parkingPosition'):
                        position = parking.parkingPosition
                        print(f"   Latitud: {position.latitude.value if hasattr(position, 'latitude') and position.latitude else 'N/A'}")
                        print(f"   Longitud: {position.longitude.value if hasattr(position, 'longitude') and position.longitude else 'N/A'}")
                
                else:
                    print("   ⚠️  Sin información de ubicación")
                    
            except Exception as e:
                print(f"   ❌ Error obteniendo ubicación: {e}")
            
            # Climatización
            print(f"\n🌡️  Climatización:")
            try:
                if hasattr(vehicle, 'domains') and Domain.CLIMATISATION in vehicle.domains:
                    climate = vehicle.domains[Domain.CLIMATISATION]
                    
                    if hasattr(climate, 'climatisationStatus'):
                        status = climate.climatisationStatus
                        print(f"   Estado: {status.climatisationState.value if hasattr(status, 'climatisationState') and status.climatisationState else 'N/A'}")
                        print(f"   Temperatura objetivo: {status.targetTemperature_C.value if hasattr(status, 'targetTemperature_C') and status.targetTemperature_C else 'N/A'}°C")
                
                else:
                    print("   ⚠️  Sin información de climatización")
                    
            except Exception as e:
                print(f"   ❌ Error obteniendo climatización: {e}")
        
        print(f"\n✅ Prueba completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")
        logger.exception("Error detallado:")
        return False
    
    finally:
        try:
            if 'weconnect' in locals():
                await weconnect.logout()
                print("👋 Logout exitoso")
        except:
            pass

def main():
    """Función principal"""
    print("🔧 Test de API Cupra WeConnect")
    print("=" * 40)
    
    # Verificar versión de Python
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ requerido")
        return
    
    # Ejecutar test
    try:
        result = asyncio.run(test_cupra_api())
        
        if result:
            print("\n🎉 Test completado exitosamente!")
        else:
            print("\n💥 Test falló")
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrumpido por el usuario")
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")

if __name__ == "__main__":
    main()
