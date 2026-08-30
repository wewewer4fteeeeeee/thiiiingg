// @ts-nocheck
const api = "https://explodingcar.pythonanywhere.com/"
const keepAlive = [];

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

        const tryFieldPatch = (obj, fieldName) => {
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
                    onEnter(args) {
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
                    onLeave(retval) { retval.replace(Il2Cpp.Boolean(false).handle); }
                });
            }
            const vpnUpdate = vpn.tryMethod("Update");
            if (vpnUpdate) {
                Interceptor.replace(vpnUpdate.virtualAddress, new NativeCallback(() => {}, 'void', []));
            }
            const vpnCtor = vpn.tryMethod(".ctor");
            if (vpnCtor) {
                Interceptor.attach(vpnCtor.virtualAddress, {
                    onEnter(args) {
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
                    onLeave(retval) { retval.replace(Il2Cpp.Boolean(false).handle); }
                });
            }
            const fridaUpdate = frida.tryMethod("Update");
            if (fridaUpdate) {
                Interceptor.replace(fridaUpdate.virtualAddress, new NativeCallback(() => {}, 'void', []));
            }
            const portCheck = frida.tryMethod("IsFridaPortOpen");
            if (portCheck) {
                Interceptor.attach(portCheck.virtualAddress, {
                    onLeave(retval) { retval.replace(Il2Cpp.Boolean(false).handle); }
                });
            }
        } catch(e) {}

        try {
            const AS = asm.image.class("AnimalCompany.AppStartup");
            const gc = AS.tryMethod("GetAppStartupConfig");
            if (gc) {
                Interceptor.attach(gc.virtualAddress, {
                    onEnter(args) { this.p = args[gc.parameterCount === 7 ? 4 : 3]; },
                    onLeave(retval) {
                        try { this.p.writePointer(getNew().handle); } catch(e) {}
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
                    onEnter(args) { this.self = new Il2Cpp.Object(args[0]); },
                    onLeave(args) { tryFieldPatch(this.self, "_apiOrigin"); }
                });
            }
        } catch(e) {}

        try {
            const IA = asm.image.class("AnimalCompany.InitializeAppAction");
            const ctor = IA.tryMethod(".ctor");
            if (ctor) {
                Interceptor.attach(ctor.virtualAddress, {
                    onEnter(args) { this.self = new Il2Cpp.Object(args[0]); },
                    onLeave(retval) { tryFieldPatch(this.self, "_apiOrigin"); }
                });
            }
            const exec = IA.tryMethod("Execute", 1);
            if (exec) {
                Interceptor.attach(exec.virtualAddress, {
                    onEnter(args) { this.self = new Il2Cpp.Object(args[0]); },
                    onLeave(retval) { tryFieldPatch(this.self, "_apiOrigin"); }
                });
            }
        } catch(e) {}

        try {
            const appFlags = asm.image.class("AnimalCompany.AppFlags");
            if (appFlags) {
                for (const methodName of ["get_isHalloween","get_isThanksgiving","get_isSnowStorm","get_isHeavyRain"]) {
                    try {
                        const method = appFlags.tryMethod(methodName);
                        if (method) {
                            Interceptor.attach(method.virtualAddress, {
                                onLeave(retval) { try { retval.value = false; } catch(e) {} }
                            });
                        }
                    } catch(e) {}
                }
            }
        } catch(e) {}

        try {
            const seasonalEventManager = asm.image.class("AnimalCompany.SeasonalEventManager");
            if (seasonalEventManager) {
                for (const methodName of ["get_isSnowStormActive","get_isHeavyRainActive"]) {
                    try {
                        const method = seasonalEventManager.tryMethod(methodName);
                        if (method) {
                            Interceptor.attach(method.virtualAddress, {
                                onLeave(retval) { try { retval.value = false; } catch(e) {} }
                            });
                        }
                    } catch(e) {}
                }
                try {
                    const instance = seasonalEventManager.field("instance");
                    if (instance) {
                        const inst = instance.value;
                        if (inst) {
                            const self = new Il2Cpp.Object(inst);
                            for (const fname of ["_isSnowStormActive","_isHeavyRainActive"]) {
                                try { const f = self.field(fname); if (f) f.value = Il2Cpp.Boolean(false); } catch(e) {}
                            }
                            for (const fname of ["_snowStormAudioSource","_heavyRainAudioSource"]) {
                                try {
                                    const af = self.field(fname);
                                    if (af) { const a = af.value; if (a) { const v = a.field("volume"); if (v) v.value = Il2Cpp.Single(0); } }
                                } catch(e) {}
                            }
                        }
                    }
                } catch(e) {}
            }
        } catch(e) {}

        try {
            const GAMEDATA_PATH = "/sdcard/Android/data/woosterGames.animalCompany/gamedata_url.txt";
            const nakamaAsm = Il2Cpp.domain.assembly("NakamaRuntime");
            if (nakamaAsm) {
                const adapter      = nakamaAsm.image.class("Nakama.UnityWebRequestAdapter");
                const getInstance  = adapter.method("get_Instance");
                const sendAsync    = adapter.method("SendAsync");

                if (getInstance && sendAsync) {
                    const instance = getInstance.invoke();

                    if (instance && !instance.isNull()) {
                        const mscorlib  = Il2Cpp.domain.assembly("mscorlib").image;
                        const SystemUri = mscorlib.class("System.Uri");
                        const uri       = SystemUri.alloc();
                        SystemUri.method(".ctor", 1).invoke(uri, Il2Cpp.string(`${api}changegamedatarples`));

                        const DictClass = mscorlib.class("System.Collections.Generic.Dictionary`2[[System.String],[System.String]]");
                        const headers   = DictClass.alloc();
                        DictClass.method(".ctor", 0).invoke(headers);

                        let gamedataUrl = "";
                        try {
                            const File     = mscorlib.class("System.IO.File");
                            const readText = File.method("ReadAllText", 1);
                            gamedataUrl    = readText.invoke(Il2Cpp.string(GAMEDATA_PATH)).content.trim();
                        } catch(e) {
                            console.log("[gamedata] read failed: " + e);
                        }

                        const bodyStr   = JSON.stringify({ gamedata: gamedataUrl });
                        const Encoding  = mscorlib.class("System.Text.Encoding");
                        const utf8      = Encoding.property("UTF8").getter.invoke();
                        const bodyBytes = Encoding.method("GetBytes", 1).invoke(utf8, Il2Cpp.string(bodyStr));

                        sendAsync.invoke(
                            instance,
                            Il2Cpp.string("POST"),
                            uri,
                            headers,
                            bodyBytes,
                            Il2Cpp.Int32(30),
                            Il2Cpp.ValueType.zero
                        );

                        console.log("[gamedata] POST fired: " + gamedataUrl);
                    }
                }
            }
        } catch(e) {
            console.log("[gamedata] error: " + e);
        }

        console.log("[Explodings version swapper] Ready!");
        
    } catch(e) {
        console.log("[Explodings version swapper] Error", e, e.stack);
    }
});
