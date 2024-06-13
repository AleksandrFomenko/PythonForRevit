import clr
import System
clr.AddReference('RevitAPI')
clr.AddReference("RevitServices")
import RevitServices
from Autodesk.Revit.ApplicationServices import Application
from Autodesk.Revit import DB
from Autodesk.Revit.DB import FilteredElementCollector as FEC
from System.Collections.Generic import List


# Parameters

parameter_sort = "Сортировка"

def search_parameter (item: DB.Element, parameter: DB.Parameter):

    par = item.LookupParameter(parameter)
    if par:
        return par
    
    type = doc.GetElement(item.GetTypeId())
    if type:
        par = type.LookupParameter(parameter)
        if par:
            return par
        

def set_param (item: DB.Element, param: str, value) -> None:

    parameter = search_parameter(item, param)
    if parameter and not parameter.IsReadOnly:
        parameter.Set(value)
        
map_cat = {
    DB.BuiltInCategory.OST_DuctCurves : 20, # трубы
    DB.BuiltInCategory.OST_MechanicalEquipment : 10,  # оборудование
    DB.BuiltInCategory.OST_DuctFitting : 30, # фитинги труб
    DB.BuiltInCategory.OST_DuctAccessory : 40, # арматура труб
    DB.BuiltInCategory.OST_DuctInsulations : 50 # изоляция труб
}
map_cat_ids = {DB.Category.GetCategory(doc, cat).Id.IntegerValue: value for cat, value in map_cat.items()}

items = (
    FEC(doc,doc.ActiveView.Id).
    WhereElementIsNotElementType().
    ToElements()
    )

def sort_pipe_category () -> None:
    for item in items:
        cat = item.Category
        print(cat)
        value = map_cat_ids.get(cat.Id.IntegerValue, 99)
        set_param (item, parameter_sort, value)
        
    



with DB.Transaction(doc, "Set Parameters") as t:

    t.Start()

    sort_pipe_category ()
    items = (
    FEC(doc, doc.ActiveView.Id).
    OfCategory(DB.BuiltInCategory.OST_DuctInsulations).
    WhereElementIsNotElementType().
    ToElements()
    )
    for item in items:
        y = item.get_Parameter(DB.BuiltInParameter.RBS_CURVE_SURFACE_AREA).AsDouble()
        y2 = DB.UnitUtils.ConvertFromInternalUnits(y, DB.UnitTypeId.SquareMeters)
        u = item.LookupParameter("ADSK_Количество").Set(y2)

    
    t.Commit()
