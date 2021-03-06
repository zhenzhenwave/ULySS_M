from astroquery.vizier import Vizier
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
# %matplotlib qt

def checkCol(cata):
    dict = {
    'Name' : ['Name', 'Star', 'name', 'SimbadName', 'Simbad'],
    'RA' : ['RA', '_RA.icrs', '_RA', 'ra', 'RAJ2000'],
    'DEC' : ['DEC', 'DE', '_DE.icrs', '_DE', 'dec', 'DEJ2000'],
    'SpT' : ['SpT', 'SpType'],
    'Teff' : ['Teff', 'teff', 'Fe_H_Teff'],
    'logg' : ['logg', 'log_g_', 'Fe_H_logg'],
    'Fe_H' : ['Fe_H', '__Fe_H_', 'Fe_H_Teff', 'Fe_H_Fe_H'],
    'ref_name' : ['ref_name', 'Ref_Name']
    }
    
    for cols in cata.colnames:
        for key in dict.keys():
            if cols in dict[key]:
                dict[key] = cols
    for key in dict.keys():
        if type(dict[key]) == list:
            dict[key] = None

    return dict

def getVizier(table_names):

    Vizier.ROW_LIMIT = -1
    catalog_names = table_names
    catalog_list = Vizier.get_catalogs(catalog_names)
    print(catalog_list) 
    cata_As = []

    for i in range(len(catalog_list)):
        cata = catalog_list[i]
        print('----- [%d out of %d] ----- \n' %(i+1, len(catalog_list)))
        print('Meta:', cata.meta)
        print('Columns:', cata.colnames) 
        
        dict = checkCol(cata)
        print('\n found useful columns: ', dict)

        if (dict['Name'] or dict['RA']) == None:
            print('\n Skip : Cant locate catalog stars: Missing Name and Coord')
            continue
        else:
            flag = input('Are you sure to proceed? (yes/no)')

        if flag in ['yes', 'y', '1']:
            cata = cata.to_pandas()
            cata_2 = cata.copy()
            for key in dict.keys():
                if dict[key] != None:
                    cata_2[key] = cata[dict[key]]
                else:
                    cata_2[key] = None
            cata_2 = cata_2[dict.keys()]
            cata_2.loc[:, 'ref_name'] = catalog_names[i]
            ref_table = cata_A(cata_2)
            cata_As.append(ref_table)
        elif flag in ['no', 'n', '0']:
            continue

        else:
            break
    return cata_As

class cata_A(pd.DataFrame):
    def fillTGM(self):
        '''
        find losting TGM & SpT parameters via SIMBAD query, with given name
        '''
        customSimbad = Simbad()
        customSimbad.add_votable_fields('sptype','fe_h','typed_id')
        
        # 查询

        try:
            res = customSimbad.query_objects(self.Name).to_pandas()
        except:
            print('Error finding TGM: ',res)
        finally:
            if self.Teff[0] == None:
                self.Teff = res['Fe_H_Teff']
                print('quert from SIMBAD: Teff')
            if self.logg[0] == None:
                self.logg = res['Fe_H_log_g']
                print('quert from SIMBAD: logg')
            if self.Fe_H[0] == None:
                self.Fe_H = res['Fe_H_Fe_H']
                print('quert from SIMBAD: Fe_H')
            if self.SpT[0] == None:
                self.SpT = res['SP_TYPE']
                print('quert from SIMBAD: SpT')
        
    def fillCoord(self):
        try: 
            float(self.RA[1])
            pass
        except:
            for i in range(len(self.Name)):
                try:
                    c = SkyCoord.from_name(self.Name[i])
                except:
                    print('Error finding coord: ' , self.Name[i],' ,', self.RA[i], self.DEC[i], ' using "hms2deg"')
                    if self.RA[i] == None:
                        print('Cannt find coord, Drop :',self.Name[i])
                        self.drop(self.index[i], inplace=True) 
                        break
                    else: 
                        a, b = self.RA[i], self.DEC[i]
                        h,m,s = a.split(' ')
                        if float(h)<24:
                            ra = h+'h'+m+'m'+s+'s'
                        else:
                            ra = h+'d'+m+'m'+s+'s'
                        d,m,s = b.split(' ')
                        dec = d+'d'+m+'m'+s+'s'
                        c = SkyCoord(ra,dec)
                finally:
                    ra,dec = c.ra.deg, c.dec.deg
                    self.RA[i] = ra
                    self.DEC[i] = dec

    def Mstars(self):
        filter_Teff = ((self.Teff < 5000) & (self.Teff > 3100))
        filter_SpT = self.SpT.str.contains("M")
        filter_DEC = ((self.DEC < 60.0) & (self.DEC > -10.0))

        return (filter_DEC & filter_Teff & filter_SpT)

    def tgm2np(self):
        self.Teff = self.Teff.to_numpy()
        self.logg = self.logg.to_numpy()
        self.Fe_H = self.Fe_H.to_numpy()
        self.RA = self.RA.to_numpy()
        self.DEC = self.DEC.to_numpy()

    def draw_parameter_space(self):
        tgm = np.array([self.Teff.to_numpy(), self.logg.to_numpy(), self.Fe_H.to_numpy()])
        
        # --- log Teff v.s. log g ----------
        fig = plt.figure(figsize = [10, 6])
        ax = fig.add_subplot(111)
        ax.plot(np.log10(tgm[0]), tgm[1], 'g.', markersize=10)

        ax.set_xlabel('$log \ T_{eff}$', fontsize=18)
        ax.set_ylabel('$log \ g$', fontsize=18)
        plt.gca().invert_xaxis()
        plt.gca().invert_yaxis()

        file_name = 'TvsG.png' 
        plt.savefig(file_name, bbox_inches='tight')
        plt.show()
        print('Saved to ' + file_name)

        # --- log Teff v.s. Fe_H ------------
        fig = plt.figure(figsize = [10, 6])
        ax = fig.add_subplot(111)
        ax.plot(np.log10(tgm[0]), tgm[2], 'k.', markersize=10)

        ax.set_xlabel('$log \ T_{eff}$', fontsize=18)
        ax.set_ylabel('Fe/H', fontsize=18)
        plt.gca().invert_xaxis()

        file_name = 'TvsM.png' 
        plt.savefig(file_name, bbox_inches='tight')
        plt.show()
        print('Saved to ' + file_name)

        return 'done'

