"""Render-Einstellungen, Collections und Steuerung."""
import bpy

from .util import collection, layer_collection, neues_objekt, setze

SAMMLUNGEN = [
    ("00_Steuerung", None), ("01_Gelaende", None), ("01a_Beete", "01_Gelaende"),
    ("02_Architektur", None), ("03_Innenraum", None), ("04_Hardscape", None),
    ("05_Pflanzen", None), ("05a_Rasen", "05_Pflanzen"), ("05b_Graeser", "05_Pflanzen"),
    ("05c_Stauden", "05_Pflanzen"), ("05d_Straeucher", "05_Pflanzen"), ("05e_Baeume", "05_Pflanzen"),
    ("05f_Kulisse", "05_Pflanzen"), ("06_Licht", None), ("07_Kameras", None),
    ("98_Masken", None), ("Maske_Rasen", "98_Masken"), ("Maske_Beet", "98_Masken"),
    ("99_Bibliothek", None), ("Bib_Halme", "99_Bibliothek"), ("Bib_Graeser", "99_Bibliothek"),
    ("Bib_Stauden", "99_Bibliothek"), ("Bib_Polster", "99_Bibliothek"), ("Bib_Kiefer", "99_Bibliothek"),
    ("01b_Wiese", "01_Gelaende"), ("01c_Heckenkern", "01_Gelaende"), ("05g_Hecke", "05_Pflanzen"),
    ("Bib_Heckenblatt", "99_Bibliothek"),
]


def render_einrichten():
    log = []
    cp = bpy.context.preferences.addons["cycles"].preferences
    cp.compute_device_type = "OPTIX"
    cp.refresh_devices()
    for d in cp.devices:
        d.use = d.type == "OPTIX"
    bpy.ops.wm.save_userpref()

    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100

    for attr, wert in [("device", "GPU"), ("samples", 1024), ("use_adaptive_sampling", True),
                       ("adaptive_threshold", 0.01), ("use_denoising", True), ("denoiser", "OPTIX"),
                       ("preview_samples", 64), ("use_preview_denoising", True), ("max_bounces", 12),
                       ("diffuse_bounces", 4), ("glossy_bounces", 4), ("transmission_bounces", 8),
                       ("transparent_max_bounces", 64)]:
        setze(sc.cycles, attr, wert, log)

    sc.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
        if setze(sc.view_settings, "look", look, []):
            break
    else:
        log.append("AgX-Look nicht gesetzt")

    r.engine = "BLENDER_EEVEE"
    e = sc.eevee
    for attr, wert in [("use_raytracing", True), ("ray_tracing_method", "SCREEN"), ("use_shadows", True),
                       ("shadow_ray_count", 2), ("shadow_step_count", 8), ("shadow_resolution_scale", 1.0),
                       ("use_volumetric_shadows", True), ("volumetric_tile_size", "4"),
                       ("taa_samples", 16), ("taa_render_samples", 128), ("use_fast_gi", True)]:
        setze(e, attr, wert, log)
    if hasattr(e, "ray_tracing_options"):
        setze(e.ray_tracing_options, "resolution_scale", "1", log)
    return {"log": log, "geraete": [(d.name, d.type, d.use) for d in cp.devices]}


def struktur():
    for name, eltern in SAMMLUNGEN:
        collection(name, eltern)
    for maske, kinder in (("Maske_Rasen", ("02_Architektur", "04_Hardscape", "01a_Beete", "01c_Heckenkern")),
                          ("Maske_Beet", ("02_Architektur", "04_Hardscape"))):
        ziel = bpy.data.collections[maske]
        for kind in kinder:
            if kind not in ziel.children:
                ziel.children.link(bpy.data.collections[kind])
    for name in ("98_Masken", "99_Bibliothek"):
        layer_collection(name).exclude = True
    for name in ("Cube", "Light", "Camera"):
        o = bpy.data.objects.get(name)
        if o is not None:
            bpy.data.objects.remove(o, do_unlink=True)
    st = bpy.data.objects.get("Steuerung")
    if st is None:
        st = neues_objekt("Steuerung", None, "00_Steuerung")
        st.empty_display_type = "PLAIN_AXES"
    if "modus" not in st:
        st["modus"] = 0.0
    st.id_properties_ui("modus").update(
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
        description="0 = Laufen (schnell), 1 = Schönbild (volle Dichte)")
    return {"sammlungen": sorted(c.name for c in bpy.data.collections)}
