import clr
import System
clr.AddReference('RevitAPI')
clr.AddReference("RevitServices")
from Autodesk.Revit import DB
from Autodesk.Revit.DB import DirectShape as DS
from System.Collections.Generic import List
from Autodesk.Revit.DB import FilteredElementCollector as FEC


class Units:
    def __init__(self):
        pass

    def set_value_to_param(self, item, parameter_name, value):
        par = item.LookupParameter(parameter_name)
        if par and not par.IsReadOnly:
            if par.StorageType == DB.StorageType.String:
                par.Set(str(value))
                return
            if par.StorageType == DB.StorageType.Integer:
                par.Set(value)
                return
            if par.StorageType == DB.StorageType.Double:
                par.Set(value)
                return

    def return_geom(self, item):
        opt = DB.Options()
        lt = List[DB.GeometryObject]()
        geometry_item = item.get_Geometry(opt)
        for geom_obj in geometry_item:
            if isinstance(geom_obj, DB.GeometryInstance):
                instance_geom = geom_obj.GetInstanceGeometry()
                geom_list = [geom for geom in instance_geom if isinstance(geom, DB.Solid) and geom.Volume > 0]
                if len(geom_list) == 1:
                    for geom in geom_list:
                        lt.Add(geom)
                elif len(geom_list) != 0:
                    largest_geom = max(geom_list, key=lambda geom: geom.Volume)
                    for geom in geom_list:
                        if geom != largest_geom:
                            lt.Add(geom)
        return lt

    def create_shape(self, category, lt):
        direct_shape = DS.CreateElement(doc, category)
        direct_shape.SetShape(lt)


class Stairs:
    # Категория модели в контексте
    cat_id = DB.ElementId(DB.BuiltInCategory.OST_Floors)
    un = Units()

    # Площадки
    landings = (
        FEC(doc)
        .OfCategory(DB.BuiltInCategory.OST_StairsLandings)
        .WhereElementIsNotElementType()
        .ToElements()
    )

    # Марши
    runs = (
        FEC(doc)
        .OfCategory(DB.BuiltInCategory.OST_StairsRuns)
        .WhereElementIsNotElementType()
        .ToElements()
    )

    def __init__(self):
        pass

    def create_shape_landings(self):
        for land in Stairs.landings:
            geom = self.un.return_geom(land)
            self.un.create_shape(self.cat_id, geom)

    def create_shape_runs(self):
        for run in Stairs.runs:
            geom = self.un.return_geom(run)
            self.un.create_shape(self.cat_id, geom)


with DB.Transaction(doc, "Create Shapes") as t:
    t.Start()

    st = Stairs()
    st.create_shape_landings()
    st.create_shape_runs()

    t.Commit()
