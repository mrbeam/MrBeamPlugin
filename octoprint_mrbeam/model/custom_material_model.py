
class CustomMaterialModel:
    def __init__(self, material_key, material, laser_cutter_mode, laser_model, plugin_v, device_model):
        self.colors = material.get("colors", [])
        self.custom = True
        self.description = material.get("description", "")
        self.device_model = device_model
        self.hints = material.get("hints", "")
        self.img = material.get("img", "null")
        self.laser_cutter_mode = laser_cutter_mode
        self.laser_model = laser_model
        self.name = material.get("name")
        self.safety_notes = material.get("safety_notes", "")
        self.v = plugin_v

        self.material_key = self.generate_material_key(material_key)

    def __str__(self):
        return "CustomMaterialModel(name='{0}', description='{1}')".format(self.name, self.description)

    def __repr__(self):
        return (
            "CustomMaterialModel("
            "key='{0}', "
            "colors={1}, "
            "custom={2}, "
            "description='{3}', "
            "device_model='{4}', "
            "hints='{5}', "
            "img='{6}', "
            "laser_cutter_mode='{7}', "
            "laser_model='{8}', "
            "name='{9}', "
            "safety_notes='{10}', "
            "v={11})"
            .format(
                self.material_key,
                self.colors,
                self.custom,
                self.description,
                self.device_model,
                self.hints,
                self.img,
                self.laser_cutter_mode,
                self.laser_model,
                self.name,
                self.safety_notes,
                self.v
            )
        )

    def to_dict(self):
        material = vars(self)
        # material.pop("material_key")
        return material

    def generate_material_key(self, material_key):
        return "{} - {}".format(material_key, self.laser_cutter_mode)
