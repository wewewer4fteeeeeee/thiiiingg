// @ts-nocheck
const api = "whyy are you hear bub?"
const keepAlive: any[] = [];
Il2Cpp.perform(() => {
    console.log("[Explodings version swapper] made by exploding car :3");
    try {
        const asm = Il2Cpp.domain.assembly("AnimalCompany");
        if (!asm) { console.log("[Explodings version swapper] AnimalCompany not found"); return; }
        const getNew = () => { const s = Il2Cpp.string(api); keepAlive.push(s); return s; };

        const tryFieldPatch = (obj: any, fieldName: string) => {
            try { obj.field(fieldName).value = getNew();  return true; } catch (e) {}
            try { obj.handle.add(0x38).writePointer(getNew().handle); return true; } catch (e) {}
            try { obj.handle.add(0x78).writePointer(getNew().handle);  return true; } catch (e) {}
            return false;
        };

        try {
            const AS = asm.image.class("AnimalCompany.AppStartup");
            const gc = AS.tryMethod("GetAppStartupConfig");
            if (gc) {
                const m = gc;
                Interceptor.attach(m.virtualAddress, {
                    onEnter(args:any){ this.p = args[m.parameterCount === 7 ? 4 : 3]; },
                    onLeave(retval:any){
                        try{ const s=getNew(); this.p.writePointer(s.handle); }catch(e){}
                    }
                });
            }
        } catch(e){ console.log("GetAppStartupConfig hook fail",e); }

        try {
            const AS = asm.image.class("AnimalCompany.AppStartup");
            for(const name of ["Awake","Start"]){
                const m = AS.tryMethod(name,0);
                if(!m) continue;
                Interceptor.attach(m.virtualAddress,{
                    onEnter(args:any){ this.self = new Il2Cpp.Object(args[0]); },
                    onLeave(args:any){ tryFieldPatch(this.self,"_apiOrigin"); }
                });
            }
        } catch(e){}

        try {
            const IA = asm.image.class("AnimalCompany.InitializeAppAction");
            const ctor = IA.tryMethod(".ctor");
            if(ctor){
                Interceptor.attach(ctor.virtualAddress,{
                    onEnter(args:any){ this.self = new Il2Cpp.Object(args[0]); },
                    onLeave(retval:any){ tryFieldPatch(this.self,"_apiOrigin"); }
                });
            }
            const exec = IA.tryMethod("Execute",1);
            if(exec){
                Interceptor.attach(exec.virtualAddress,{
                    onEnter(args:any){ this.self = new Il2Cpp.Object(args[0]); },
                    onLeave(retval:any){ tryFieldPatch(this.self,"_apiOrigin"); }
                });
            }
        } catch(e){}

        
    } catch(e){ console.log("[Explodings version swapper] Error",e, (e as any).stack); }
});