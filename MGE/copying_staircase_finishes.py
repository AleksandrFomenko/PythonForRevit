import clr
import System
clr.AddReference('RevitAPI')
clr.AddReference("RevitServices")
from Autodesk.Revit import DB
from Autodesk.Revit.DB import DirectShape as ds
from System.Collections.Generic import List
from Autodesk.Revit.DB import FilteredElementCollector as FEC

class units:
    def __init__(self):
        pass
    def _set_value_to_par(self,item,parameter_name,value):
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
                instanceGeom = geom_obj.GetInstanceGeometry()
                geom_list = [geom for geom in instanceGeom if isinstance(geom, DB.Solid) and geom.Volume > 0]
                if len(geom_list) == 1:
                    for geom in geom_list:
                        lt.Add(geom)
                elif len(geom_list) != 0:
                    largest_geom = max(geom_list, key=lambda geom: geom.Volume)
                    for geom in geom_list:
                        if geom != largest_geom:
                            lt.Add(geom)
                    
        return lt
    def create_shape(self,category,lt):
        direct_shape = ds.CreateElement(doc,category)
        direct_shape.SetShape(lt)


class stairs:
    #Категория модели в контексте
    cat_id = DB.ElementId(DB.BuiltInCategory.OST_Floors)
    un = units()
    #Площадки
    _landings_ = (
        FEC(doc).
        OfCategory(DB.BuiltInCategory.OST_StairsLandings).
        WhereElementIsNotElementType().
        ToElements()
    )
    #Марши
    _runs_ = (
        FEC(doc).
        OfCategory(DB.BuiltInCategory.OST_StairsRuns).
        WhereElementIsNotElementType().
        ToElements()
    )
    def __init__(self):
        pass
    def create_shape_langings(self):
        for land in stairs._landings_:
            geom = self.un.return_geom(land)
            self.un.create_shape(self.cat_id,geom)
    def create_shape_runs(self):
        for land in stairs._runs_:
            geom = self.un.return_geom(land)
            self.un.create_shape(self.cat_id,geom)
    




with DB.Transaction(doc,"qwe") as t:
    t.Start()

    st = stairs()
    st.create_shape_langings()
    st.create_shape_runs()

    t.Commit()

