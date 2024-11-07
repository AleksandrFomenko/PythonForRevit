import clr

clr.AddReference('RevitAPI')

from Autodesk.Revit import DB
from Autodesk.Revit.DB import FilteredElementCollector as FEC
from abc import ABC, abstractmethod
import math

# shapes
shape_rectangular = DB.ConnectorProfileType.Rectangular
shape_round = DB.ConnectorProfileType.Round

# mass of corners and bolts
# Масса удельная кста
mass_corner = 3.77
mass_bolt = 0.395

# запас типо в %
reserve = 10

# Parameters
parameter_name_without_iso = "Вес креплений для воздуховодов без изоляции"
parameter_name_with_iso = "Вес креплений для воздуховодов с изоляцией"

def get_parameter(item: DB.Element, parameter_name: str):
    """
    Возвращает параметр элемента или типа элемента
    """
    parameter = item.LookupParameter(parameter_name)
    if parameter:
        return parameter

    type_elem = doc.GetElement(item.GetTypeId())
    if not type_elem:
        return None

    parameter = type_elem.LookupParameter(parameter_name)
    if parameter:
        return parameter

    print(f"Не нашел параметр: {parameter_name}")
    return None


class IDuctType(ABC):
    step_meters = 4.5
    res_with_iso = 0
    res_all = 0

    @abstractmethod
    def process(self):
        pass

    def biggest_side(self, duct: DB.Element):
        connector = list(duct.ConnectorManager.Connectors)[0]
        if connector.Shape == shape_rectangular:
            height = connector.Height * 304.8
            width = connector.Width * 304.8
            return max(height, width)
        elif connector.Shape == shape_round:
            return connector.Radius * 2 * 304.8
        else:
            raise ValueError("Неподдерживаемый тип соединителя")

    def get_length(self, duct: DB.Element):
        return duct.get_Parameter(DB.BuiltInParameter.CURVE_ELEM_LENGTH).AsDouble() * 304.8 / 1000

    def get_number_fasteners(self, duct: DB.Element):
        length = self.get_length(duct)
        return math.ceil(length / self.step_meters)

    def get_length_corner(self, duct):
        return (self.biggest_side(duct) + 200)/1000

    def get_length_bolt(self, duct):
        side = self.biggest_side(duct)
        if side < 700:
            return 0.8

        return side/1000 + 0.1

    def get_mass_corner(self, duct):
        len = self.get_length_corner(duct)
        number_result = self.get_number_fasteners(duct)
        mass = mass_corner
        res = ((100 + reserve) / 100)
        return math.ceil(len * number_result * mass * res)

    def get_mass_bolt(self, duct):
        len = self.get_length_bolt(duct)
        number_result = self.get_number_fasteners(duct) * 2
        mass = mass_bolt
        res = ((100 + reserve) / 100)
        return math.ceil(len * number_result * mass * res)

    def setter(self, duct):
        parameter_without_iso = get_parameter(duct, parameter_name_without_iso)
        parameter_with_iso = get_parameter(duct, parameter_name_with_iso)
        result = self.get_mass_bolt(duct) + self.get_mass_corner(duct)
        self.res_all += result

        if duct.get_Parameter(DB.BuiltInParameter.RBS_REFERENCE_INSULATION_TYPE).AsString():
            self.res_with_iso += result
            if parameter_with_iso and not parameter_with_iso.IsReadOnly:
                if parameter_with_iso.StorageType == DB.StorageType.String:
                    parameter_with_iso.Set(str(result))

                if parameter_with_iso.StorageType == DB.StorageType.Integer:
                    parameter_with_iso.Set(result)

                if parameter_with_iso.StorageType == DB.StorageType.Double:
                    parameter_with_iso.Set(result)
        else:
            if parameter_without_iso and not parameter_without_iso.IsReadOnly:
                if parameter_without_iso.StorageType == DB.StorageType.String:
                    parameter_without_iso.Set(str(result))

                if parameter_without_iso.StorageType == DB.StorageType.Integer:
                    parameter_without_iso.Set(result)

                if parameter_without_iso.StorageType == DB.StorageType.Double:
                    parameter_without_iso.Set(result)




class RoundVerticalDuct(IDuctType):
    def __init__(self, duct):
        self.duct = duct

    def process(self):
        self.setter(duct)


class RectangularVerticalDuct(IDuctType):
    def __init__(self, duct):
        self.duct = duct

    def process(self):
        self.setter(duct)


class RoundHorizontalDuct(IDuctType):
    def __init__(self, duct):
        self.duct = duct
        side = self.biggest_side(duct)
        self.step_meters = 3 if side < 400 else 4

    def process(self):
        self.setter(duct)


class RectangularHorizontalDuct(IDuctType):
    def __init__(self, duct):
        self.duct = duct
        side = self.biggest_side(duct)
        self.step_meters = 3 if side < 400 else 4

    def process(self):
        self.setter(duct)


class Worker:
    def __init__(self, duct_type: IDuctType):
        self.ductType = duct_type
        self.total_res_all = 0
        self.total_res_with_iso = 0

    def execute(self):
        self.ductType.process()
        # Аккумулируем значения по всем воздуховодам
        self.total_res_all += self.ductType.res_all
        self.total_res_with_iso += self.ductType.res_with_iso


def get_shape(duct):
    # Определяет форму и ориентацию воздуховода
    connector = list(duct.ConnectorManager.Connectors)[0]
    line = duct.Location.Curve.Tessellate()
    xyz_1 = line[0]
    xyz_2 = line[1]

    is_horizontal = xyz_1.Z == xyz_2.Z

    if connector.Shape == shape_round:
        return RoundHorizontalDuct(duct) if is_horizontal else RoundVerticalDuct(duct)
    elif connector.Shape == shape_rectangular:
        return RectangularHorizontalDuct(duct) if is_horizontal else RectangularVerticalDuct(duct)
    else:
        raise ValueError("Неизвестная форма воздуховода")



with DB.Transaction(doc, "Обработка воздуховодов") as t:
    t.Start()

    ducts = FEC(doc) \
        .OfCategory(DB.BuiltInCategory.OST_DuctCurves) \
        .WhereElementIsNotElementType() \
        .ToElements()

    total_res_all = 0
    total_res_with_iso = 0

    for duct in ducts:
        try:
            duct_type = get_shape(duct)
            worker = Worker(duct_type)
            worker.execute()
            total_res_all += worker.total_res_all
            total_res_with_iso += worker.total_res_with_iso
        except Exception as e:
            print(f"Ошибка при обработке воздуховода {duct.Id}: {e}")

    print(f"Вес всех воздуховодов {total_res_all}")
    print(f"Вес воздуховодов c изоляцией {total_res_with_iso}")

    t.Commit()
