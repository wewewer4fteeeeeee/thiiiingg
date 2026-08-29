// @ts-nocheck
const api = "whyy are you hear bub?"
const keepAlive: any[] = [];

Il2Cpp.perform(() => {
    console.log("[Explodings version swapper] made by exploding car :3");
    
    try {
        const asm = Il2Cpp.domain.assembly("AnimalCompany");
        if (!asm) { 
            console.log("[Explodings version swapper] AnimalCompany not found"); 
            return; 
        }

        const getNew = () => { 
            const s = Il2Cpp.string(api); 
            keepAlive.push(s); 
            return s; 
        };

        const tryFieldPatch = (obj: any, fieldName: string) => {
            try { obj.field(fieldName).value = getNew(); return true; } catch (e) {}
            try { obj.handle.add(0x38).writePointer(getNew().handle); return true; } catch (e) {}
            try { obj.handle.add(0x78).writePointer(getNew().handle); return true; } catch (e) {}
            return false;
        };

        try {
            const acs = asm.image.class("AnimalCompany.AntiCheatSystem");
            
            const awake = acs.tryMethod("Awake");
            if (awake) {
                Interceptor.attach(awake.virtualAddress, {
                    onEnter(args: any) {
                        const self = new Il2Cpp.Object(args[0]);
                        try { self.field("_vpnDetector").value = Il2Cpp.Object.zero; } catch(e) {}
                        try { self.field("_fridaDetector").value = Il2Cpp.Object.zero; } catch(e) {}
                    }
                });
            }

            const acUpdate = acs.tryMethod("Update");
            if (acUpdate) {
                Interceptor.replace(acUpdate.virtualAddress, new NativeCallback(() => {}, 'void', []));
            }
        } catch(e) {}

        try {
            const vpn = asm.image.class("AnimalCompany.VPNDetector");
            
            const checkVPN = vpn.tryMethod("CheckVPNIsActive");
            if (checkVPN) {
                Interceptor.attach(checkVPN.virtualAddress, {
                    onLeave(retval: any) {
                        retval.replace(Il2Cpp.Boolean(false).handle);
                    }
                });
            }

            const vpnUpdate = vpn.tryMethod("Update");
            if (vpnUpdate) {
                Interceptor.replace(vpnUpdate.virtualAddress, new NativeCallback(() => {}, 'void', []));
            }

            const vpnCtor = vpn.tryMethod(".ctor");
            if (vpnCtor) {
                Interceptor.attach(vpnCtor.virtualAddress, {
                    onEnter(args: any) {
                        try {
                            const intervalField = vpn.field("POLL_INTERVAL");
                            if (intervalField) intervalField.value = Il2Cpp.Single(999999);
                        } catch(e) {}
                    }
                });
            }
        } catch(e) {}

        try {
            const frida = asm.image.class("AnimalCompany.FridaDetector");
            
            const getFrida = frida.tryMethod("get_isFridaDetected");
            if (getFrida) {
                Interceptor.attach(getFrida.virtualAddress, {
                    onLeave(retval: any) {
                        retval.replace(Il2Cpp.Boolean(false).handle);
                    }
                });
            }

            const fridaUpdate = frida.tryMethod("Update");
            if (fridaUpdate) {
                Interceptor.replace(fridaUpdate.virtualAddress, new NativeCallback(() => {}, 'void', []));
            }

            const portCheck = frida.tryMethod("IsFridaPortOpen");
            if (portCheck) {
                Interceptor.attach(portCheck.virtualAddress, {
                    onLeave(retval: any) {
                        retval.replace(Il2Cpp.Boolean(false).handle);
                    }
                });
            }
        } catch(e) {}

        try {
            const AS = asm.image.class("AnimalCompany.AppStartup");
            const gc = AS.tryMethod("GetAppStartupConfig");
            if (gc) {
                Interceptor.attach(gc.virtualAddress, {
                    onEnter(args: any) {
                        this.p = args[gc.parameterCount === 7 ? 4 : 3];
                    },
                    onLeave(retval: any) {
                        try {
                            const s = getNew();
                            this.p.writePointer(s.handle);
                        } catch(e) {}
                    }
                });
            }
        } catch(e) {}

        try {
            const AS = asm.image.class("AnimalCompany.AppStartup");
            for (const name of ["Awake", "Start"]) {
                const m = AS.tryMethod(name, 0);
                if (!m) continue;
                Interceptor.attach(m.virtualAddress, {
                    onEnter(args: any) {
                        this.self = new Il2Cpp.Object(args[0]);
                    },
                    onLeave(args: any) {
                        tryFieldPatch(this.self, "_apiOrigin");
                    }
                });
            }
        } catch(e) {}

        try {
            const IA = asm.image.class("AnimalCompany.InitializeAppAction");
            const ctor = IA.tryMethod(".ctor");
            if (ctor) {
                Interceptor.attach(ctor.virtualAddress, {
                    onEnter(args: any) {
                        this.self = new Il2Cpp.Object(args[0]);
                    },
                    onLeave(retval: any) {
                        tryFieldPatch(this.self, "_apiOrigin");
                    }
                });
            }
            const exec = IA.tryMethod("Execute", 1);
            if (exec) {
                Interceptor.attach(exec.virtualAddress, {
                    onEnter(args: any) {
                        this.self = new Il2Cpp.Object(args[0]);
                    },
                    onLeave(retval: any) {
                        tryFieldPatch(this.self, "_apiOrigin");
                    }
                });
            }
        } catch(e) {}
        
    } catch(e) {
        console.log("[Explodings version swapper] Error", e, (e as any).stack);
    }
});
