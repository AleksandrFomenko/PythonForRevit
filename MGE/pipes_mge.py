import clr
import System

clr.AddReference('RevitAPI')
clr.AddReference('RevitServices')

import RevitServices
from Autodesk.Revit import DB
from Autodesk.Revit.ApplicationServices import Application
from Autodesk.Revit.DB import FilteredElementCollector as FEC
from System.Collections.Generic import List
import time

# Parameters to set

mge_name = "МГЭ_Наименование"
mge_code = "МГЭ_Код элемента"
mge_description = "МГЭ_Обозначение"
mge_code_material = "МГЭ_Код материала"
mge_name_material = "МГЭ_Наименование материала"
mge_width_material = "МГЭ_Толщина материала"
mge_isolation = "МГЭ_Наличие изоляции"
mge_group_fire = "МГЭ_Группа горючести материала"
mge_work_pressure = "МГЭ_Рабочее давление"
mge_isolation_pipe = "МГЭ_Тип изоляции"
mge_marka = "МГЭ_Марка элемента"
mge_export_as = "IfcExportAs"
mge_export_type = "IfcExportType"

# Parameters to get

adsk_name = "ADSK_Наименование"
adsk_marka = "ADSK_Марка"


# Set/Get parameters
class Handler:
    def get_parameter(self, item: DB.Element, parameter_name: str):
        parameter = item.LookupParameter(parameter_name)
        if parameter:
            return parameter

        type = doc.GetElement(item.GetTypeId())
        if not type:
            return None

        parameter = type.LookupParameter(parameter_name)
        if parameter:
            return parameter

        print(f"не нашел параметр %s", parameter_name)
        return None

    def set_parameter(self, parameter: DB.Parameter, value) -> None:
        if parameter and not parameter.IsReadOnly:
            parameter.Set(value)

    def parse_parameter(self, parameter: DB.Parameter):
        if not parameter.HasValue:
            return None

        if parameter.StorageType == DB.StorageType.ElementId:
            return parameter.AsValueString()

        if parameter.StorageType == DB.StorageType.String:
            return parameter.AsString()

        if parameter.StorageType == DB.StorageType.Integer:
            return parameter.AsInteger()

        if parameter.StorageType == DB.StorageType.Double:
            return parameter.AsDouble()


class PipeManager:
    pipes = (
        FEC(doc).
        OfCategory(DB.BuiltInCategory.OST_PipeCurves).
        WhereElementIsNotElementType().
        ToElements()
    )

    def __init__(self, handler):
        self.handler = handler

    def get_info(self, pipe):
        dict_pipe = {
            "полиэтилен": ["ГОСТ 32415-2013", "Полиэтилен", "СТ 10 17 40 30", "Г4", 1000000],
            "водогазопровод": ["ГОСТ 3262-75", "Сталь", "СТ 10 16 50", "НГ", 1000000],
            "электросвар": ["ГОСТ 10704-91", "Сталь", "СТ 10 16 50", "НГ", 1200000],
            "медная": ["ГОСТ Р 52318-2005", "Медь", "СТ 10 16 10", "НГ", 2000000],
            "полиропилен": ["ГОСТ 26996-86", "Полипропилен", "СТ 10 17 40 10", "Г4", 1000000],
            "чугун": ["ГОСТ 6942-98", "Чугун", "СТ 10 16 70", "НГ", 800000]
        }

        par = self.handler.get_parameter(pipe, adsk_name)

        if not par:
            return None

        par_string = self.handler.parse_parameter(par)

        if not par_string:
            return None

        for key in dict_pipe:
            if key in par_string.lower():
                value_gost = dict_pipe.get(key)
                return value_gost

        return None

    # МГЭ_Рабочее давление

    def work_pressure_pipe(self, pipe):
        gi = self.get_info(pipe)

        if not gi:
            return

        work_pressure = gi[4]
        if work_pressure:
            parameter = self.handler.get_parameter(pipe, mge_work_pressure)
            self.handler.set_parameter(parameter, work_pressure)

    # МГЭ_Наименование

    def name_pipe(self, pipe):
        parameter = self.handler.get_parameter(pipe, mge_name)
        if not parameter:
            return

        # Берем из адск_наименование

        adsk_name_par = self.handler.get_parameter(pipe, adsk_name)
        value = self.handler.parse_parameter(adsk_name_par)

        if value:
            self.handler.set_parameter(parameter, value)

    # МГЭ_Марка элемента

    def marka_pipe(self, pipe):
        diam = pipe.get_Parameter(DB.BuiltInParameter.RBS_PIPE_DIAMETER_PARAM)
        diam_value = round(self.handler.parse_parameter(diam) * 304.8)

        inner_diameter_param = pipe.get_Parameter(DB.BuiltInParameter.RBS_PIPE_INNER_DIAM_PARAM)
        outer_diameter_param = pipe.get_Parameter(DB.BuiltInParameter.RBS_PIPE_OUTER_DIAMETER)

        if not inner_diameter_param or not outer_diameter_param:
            return

        inner_diameter_value = self.handler.parse_parameter(inner_diameter_param) * 304.8
        outer_diameter_value = self.handler.parse_parameter(outer_diameter_param) * 304.8
        width_pipe = round((outer_diameter_value - inner_diameter_value) / 2, 1)

        result = f'Ø{diam_value}x{width_pipe:.1f}'

        param = self.handler.get_parameter(pipe, mge_marka)
        self.handler.set_parameter(param, result)

    # МГЭ_Код элемента

    def code_pipe(self, pipe):
        parameter = self.handler.get_parameter(pipe, mge_code)
        if not parameter:
            return

        value = "ЭЛ 40 15 10 10"
        self.handler.set_parameter(parameter, value)

    # МГЭ_Обозначение

    def description_pipe(self, pipe):
        gi = self.get_info(pipe)

        if not gi:
            return

        gost = gi[0]

        parameter = self.handler.get_parameter(pipe, mge_description)
        if gost:
            self.handler.set_parameter(parameter, gost)

    # МГЭ_Код материала

    def code_material_pipe(self, pipe):
        gi = self.get_info(pipe)

        if not gi:
            return

        code_material = gi[2]

        if code_material:
            parameter = self.handler.get_parameter(pipe, mge_code_material)
            self.handler.set_parameter(parameter, code_material)

    # МГЭ_Наименование материала

    def name_material_pipe(self, pipe):
        gi = self.get_info(pipe)

        if not gi:
            return

        name_material = gi[1]
        if name_material:
            parameter = self.handler.get_parameter(pipe, mge_name_material)
            self.handler.set_parameter(parameter, name_material)

    # МГЭ_Толщина материала

    def width_pipe(self, pipe):
        inner_diameter_param = pipe.get_Parameter(DB.BuiltInParameter.RBS_PIPE_INNER_DIAM_PARAM)
        outer_diameter_param = pipe.get_Parameter(DB.BuiltInParameter.RBS_PIPE_OUTER_DIAMETER)

        if not inner_diameter_param or not outer_diameter_param:
            return

        parameter = self.handler.get_parameter(pipe, mge_width_material)
        if not parameter:
            return

        inner_diameter_value = inner_diameter_param.AsDouble() * 304.8
        outer_diameter_value = outer_diameter_param.AsDouble() * 304.8

        result = (outer_diameter_value - inner_diameter_value) / 2
        self.handler.set_parameter(parameter, result)

    # МГЭ_Группа горючести

    def group_fire_pipe(self, pipe):
        gi = self.get_info(pipe)

        if not gi:
            return

        fire_group = gi[3]
        if fire_group:
            parameter = self.handler.get_parameter(pipe, mge_group_fire)
            self.handler.set_parameter(parameter, fire_group)

    # МГЭ_Наличие изоляции

    def isolation_pipe(self, pipe):
        parameter = self.handler.get_parameter(pipe, mge_isolation)
        if not parameter:
            return

        have_isolation = pipe.get_Parameter(DB.BuiltInParameter.RBS_REFERENCE_INSULATION_TYPE).AsString()

        if not have_isolation:
            self.handler.set_parameter(parameter, 0)
            return

        self.handler.set_parameter(parameter, 1)

    # МГЭ_Тип изоляции

    def isolation_type_pipe(self, pipe):
        isolation = pipe.get_Parameter(DB.BuiltInParameter.RBS_REFERENCE_INSULATION_TYPE)

        if not isolation.HasValue:
            parameter = self.handler.get_parameter(pipe, mge_isolation_pipe)
            self.handler.set_parameter(parameter, "-")
            return

        iso_name = isolation.AsString()

        iso_width_param = pipe.get_Parameter(DB.BuiltInParameter.RBS_REFERENCE_INSULATION_THICKNESS)
        iso_width = iso_width_param.AsDouble() * 304.8

        result = f"{iso_name}, d={iso_width}"

        parameter = self.handler.get_parameter(pipe, mge_isolation_pipe)
        self.handler.set_parameter(parameter, result)

    # Параметры для трубопроводов

    def pipe_execute(self):
        for pip in self.pipes:
            self.work_pressure_pipe(pip)
            self.code_pipe(pip)
            self.name_pipe(pip)
            self.marka_pipe(pip)
            self.description_pipe(pip)
            self.code_material_pipe(pip)
            self.name_material_pipe(pip)
            self.width_pipe(pip)
            self.group_fire_pipe(pip)
            self.isolation_pipe(pip)
            self.isolation_type_pipe(pip)


class FittingManager:
    pipe_fittings = (
        FEC(doc).
        OfCategory(DB.BuiltInCategory.OST_PipeFitting).
        WhereElementIsNotElementType().
        ToElements()
    )

    def __init__(self, handler):
        self.handler = handler

    def get_info(self, fitting):
        fit_dict = {
            "врезка": ["ЭЛ 40 15 20 10", "IfcPipeFitting"],
            "заглушка": ["ЭЛ 40 15 20 15", "IfcPipeFitting"],
            "крестовина": ["ЭЛ 40 15 20 25", "IfcPipeFitting"],
            "муфта": ["ЭЛ 40 15 20 99", "IfcPipeFitting"],
            "отвод": ["ЭЛ 40 15 20 30", "IfcPipeFitting"],
            "переход": ["ЭЛ 40 15 20 40", "IfcPipeFitting"],
            "прокладка": ["ЭЛ 40 15 20 45", "IfcPipeFitting"],
            "ревизия": ["ЭЛ 40 15 20 50", "IfcDistributionChamberElement"],
            "тройник": ["ЭЛ 40 15 20 55", "IfcPipeFitting"],
            "фланец": ["ЭЛ 40 15 20 60", "IfcPipeFitting"],
            "труба": ["ЭЛ 40 15 20 35", "IfcPipeFitting"],
            "угольник": ["ЭЛ 40 15 20 30", "IfcPipeFitting"],
            "гильза": ["ЭЛ 40 15 20 99", "IfcPipeFitting"],
            "ниппель": ["ЭЛ 40 15 20 99", "IfcPipeFitting"],
            "направляющая": ["ЭЛ 40 15 20 99", "IfcPipeFitting"],
            "гайка": ["ЭЛ 40 15 20 99", "IfcPipeFitting"],
        }

        parameter = self.handler.get_parameter(fitting, adsk_name)
        if parameter:
            parameter_value = self.handler.parse_parameter(parameter)
            for key in fit_dict:
                if key in parameter_value.lower():
                    return fit_dict[key]

        parameter = fitting.Symbol.Name
        if parameter:
            for key in fit_dict:
                if key in parameter.lower():
                    return fit_dict[key]

        parameter = fitting.Symbol.FamilyName
        for key in fit_dict:
            if key in parameter.lower():
                return fit_dict[key]

    def get_gost(self, fitting):
        fit_dict = {
            "rx": "ГОСТ 32415-2013",
            "пресс-фитинг": "ГОСТ 32415-2013",
            "rautitan": "ГОСТ 32415-2013"
        }

        parameter = self.handler.get_parameter(fitting, adsk_name)
        if parameter:
            parameter_value = self.handler.parse_parameter(parameter)
            for key in fit_dict:
                if key in parameter_value.lower():
                    return fit_dict[key]

        parameter = fitting.Symbol.Name
        if parameter:
            for key in fit_dict:
                if key in parameter.lower():
                    return fit_dict[key]

        parameter = fitting.Symbol.FamilyName
        for key in fit_dict:
            if key in parameter.lower():
                return fit_dict[key]

    def export_fitting(self, fitting):
        map_fit = self.get_info(fitting)
        value = None
        if map_fit:
            value = map_fit[1]

        parameter = self.handler.get_parameter(fitting, mge_export_as)
        if not parameter:
            return
        if value:
            self.handler.set_parameter(parameter, value)

    def name_fitting(self, fitting):
        parameter = self.handler.get_parameter(fitting, mge_name)
        if not parameter:
            return

        # Берем из адск_наименование

        adsk_name_par = self.handler.get_parameter(fitting, adsk_name)
        value = self.handler.parse_parameter(adsk_name_par)

        if value:
            self.handler.set_parameter(parameter, value)

    def code_fittings(self, fitting):

        map_fit = self.get_info(fitting)
        if map_fit:
            value = map_fit[0]
        else:
            value = "ЭЛ 40 15 20 99"

        parameter = self.handler.get_parameter(fitting, mge_code)
        if not parameter:
            return
        if value:
            self.handler.set_parameter(parameter, value)

    def description_fitting(self, fitting):

        parameter = self.handler.get_parameter(fitting, mge_description)
        adsk_gost = self.handler.get_parameter(fitting, adsk_marka)
        if adsk_gost:
            value = self.handler.parse_parameter(adsk_gost)
            if value:
                if "гост" in value.lower():
                    self.handler.set_parameter(parameter, value)
                    return
        value = self.get_gost(fitting)
        if value:
            self.handler.set_parameter(parameter, value)
            return
        self.handler.set_parameter(parameter, "-")

    def material_name_code_fitting(self, fitting):

        fit_dict = {
            "сталь": ["Сталь", "СТ 10 16 50", "НГ"],
            "чугун": ["Чугун", "СТ 10 16 70", "НГ"],
            "rautitan": ["Сшитый полиэтилен", "СТ 10 17 40 30", "Г4"],
            "пластик": ["Сшитый полиэтилен", "СТ 10 17 40 30", "Г4"],
            "rehau": ["Сшитый полиэтилен", "СТ 10 17 40 30", "Г4"],
            "полиэтилен": ["Сшитый полиэтилен", "СТ 10 17 40 30", "Г4"],
            "латунь": ["Латунь", "СТ 10 02 20 25", "НГ"]
        }

        parameter = self.handler.get_parameter(fitting, adsk_name)
        material_name = None
        material_code = None
        group_fire = None
        if parameter:
            parameter_value = self.handler.parse_parameter(parameter)
            for key in fit_dict:
                if key in parameter_value.lower():
                    material_name = fit_dict[key][0]
                    material_code = fit_dict[key][1]
                    group_fire = fit_dict[key][2]

        parameter = fitting.Symbol.Name
        if parameter:
            for key in fit_dict:
                if key in parameter.lower():
                    material_name = fit_dict[key][0]
                    material_code = fit_dict[key][1]
                    group_fire = fit_dict[key][2]

        parameter = fitting.Symbol.FamilyName
        for key in fit_dict:
            if key in parameter.lower():
                material_name = fit_dict[key][0]
                material_code = fit_dict[key][1]
                group_fire = fit_dict[key][2]

        if material_name:
            parameter = self.handler.get_parameter(fitting, mge_name_material)
            self.handler.set_parameter(parameter, material_name)

        if material_code:
            parameter = self.handler.get_parameter(fitting, mge_code_material)
            self.handler.set_parameter(parameter, material_code)

        if not group_fire:
            print("не нашел")
        if group_fire:
            parameter = self.handler.get_parameter(fitting, mge_group_fire)
            self.handler.set_parameter(parameter, group_fire)

    def isolation_fitting(self, fitting):
        if fitting.SuperComponent:
            return

        param_iso = fitting.get_Parameter(DB.BuiltInParameter.RBS_REFERENCE_INSULATION_TYPE)
        if not param_iso:
            return
        param_have_iso = self.handler.get_parameter(fitting, mge_isolation)
        param_type_iso = self.handler.get_parameter(fitting, mge_isolation_pipe)

        if param_iso.AsString():
            self.handler.set_parameter(param_have_iso, True)
            param_iso_width = fitting.get_Parameter(DB.BuiltInParameter.RBS_REFERENCE_INSULATION_THICKNESS)
            if not param_iso_width:
                return

            iso_width = fitting.get_Parameter(DB.BuiltInParameter.RBS_REFERENCE_INSULATION_THICKNESS).AsDouble() * 304.8
            result = f"{param_iso.AsString()}, d={iso_width}"
            self.handler.set_parameter(param_type_iso, result)
            return

        self.handler.set_parameter(param_have_iso, False)
        self.handler.set_parameter(param_type_iso, "-")


        for item_id in fitting.GetSubComponentIds():
            param_have_iso_sub = self.handler.get_parameter(doc.GetElement(item_id), mge_isolation)
            param_type_iso_sub = self.handler.get_parameter(doc.GetElement(item_id), mge_isolation_pipe)
            self.handler.set_parameter(param_have_iso_sub, False)
            self.handler.set_parameter(param_type_iso_sub, "-")

    def width_fitting(self, fit):
        params = ["ADSK_Размер_Толщина стенки", "ADSK_Толщина стенки", "Толщина стенки_1", "Толщина стенки_2"]




    def fitting_execute(self):
        for fit in self.pipe_fittings:
            #self.export_fitting(fit)
            #self.name_fitting(fit)
            #self.code_fittings(fit)
            #self.description_fitting(fit)
            #self.material_name_code_fitting(fit)
            self.isolation_fitting(fit)




with DB.Transaction(doc, "Заполнение параметров для МГЭ") as t:
    t.Start()
    start_time = time.time()
    handler = Handler()
    pipe_manager = PipeManager(handler)
    #pipe_manager.pipe_execute()

    fitting_manager = FittingManager(handler)
    fitting_manager.fitting_execute()
    t.Commit()

    print("--- %s seconds ---" % (time.time() - start_time))
    print(f"---{(time.time() - start_time)/60} minutes ---")
