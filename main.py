import tkinter as tk
from tkinter import filedialog, messagebox
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import generate_uid, ExplicitVRLittleEndian
import datetime
from PIL import Image
import os
import uuid
from pydicom.uid import SecondaryCaptureImageStorage

class DICOMConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor JPEG para DICOM")
        self.root.geometry("500x300")
        
        # Variáveis
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.patient_name = tk.StringVar(value="Anonymous")
        self.patient_id = tk.StringVar(value=str(uuid.uuid4()))  # Gera UUID automático
        
        # Interface
        self.create_widgets()
    
    def create_widgets(self):
        # Frame principal
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # Seleção de arquivo de entrada
        tk.Label(main_frame, text="Arquivo JPEG:").grid(row=0, column=0, sticky="w", pady=5)
        tk.Entry(main_frame, textvariable=self.input_path, width=40).grid(row=0, column=1, padx=5)
        tk.Button(main_frame, text="Procurar", command=self.browse_input).grid(row=0, column=2)
        
        # Seleção de arquivo de saída
        tk.Label(main_frame, text="Arquivo DICOM:").grid(row=1, column=0, sticky="w", pady=5)
        tk.Entry(main_frame, textvariable=self.output_path, width=40).grid(row=1, column=1, padx=5)
        tk.Button(main_frame, text="Procurar", command=self.browse_output).grid(row=1, column=2)
        
        # Campos de metadados
        tk.Label(main_frame, text="Nome do Paciente:").grid(row=2, column=0, sticky="w", pady=5)
        tk.Entry(main_frame, textvariable=self.patient_name).grid(row=2, column=1, sticky="ew", columnspan=2, padx=5)
        
        tk.Label(main_frame, text="ID do Paciente:").grid(row=3, column=0, sticky="w", pady=5)
        patient_id_entry = tk.Entry(main_frame, textvariable=self.patient_id, state='readonly')
        patient_id_entry.grid(row=3, column=1, sticky="ew", columnspan=2, padx=5)
        
        # Botão para gerar novo UUID
        tk.Button(main_frame, text="Gerar Novo ID", command=self.generate_new_uuid).grid(row=4, column=1, pady=5)
        
        # Botão de conversão
        tk.Button(main_frame, text="Converter para DICOM", command=self.convert, bg="green", fg="white").grid(row=5, column=1, pady=10)
        
        # Configuração de expansão
        main_frame.columnconfigure(1, weight=1)
    
    def generate_new_uuid(self):
        """Gera um novo UUID e atualiza o campo"""
        self.patient_id.set(str(uuid.uuid4()))
    
    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="Selecione a imagem JPEG",
            filetypes=(("JPEG files", "*.jpg;*.jpeg"), ("All files", "*.*"))
        )
        if filename:
            self.input_path.set(filename)
            # Sugerir nome de saída automático
            base = os.path.splitext(filename)[0]
            self.output_path.set(f"{base}.dcm")
    
    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="Salvar arquivo DICOM como",
            defaultextension=".dcm",
            filetypes=(("DICOM files", "*.dcm"), ("All files", "*.*"))
        )
        if filename:
            self.output_path.set(filename)
    
    def convert(self):
        if not self.input_path.get():
            messagebox.showerror("Erro", "Por favor, selecione um arquivo JPEG de entrada")
            return
        
        if not self.output_path.get():
            messagebox.showerror("Erro", "Por favor, especifique um arquivo DICOM de saída")
            return
        
        try:
            self.jpeg_to_dicom(self.input_path.get(), self.output_path.get())
            messagebox.showinfo("Sucesso", "Conversão concluída com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na conversão:\n{str(e)}")
    
    def jpeg_to_dicom(self, jpeg_path, dicom_path):
        # Criar metadados básicos do arquivo
        file_meta = Dataset()
        file_meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
        file_meta.MediaStorageSOPInstanceUID = generate_uid()
        file_meta.ImplementationClassUID = generate_uid()
        file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        
        # Criar dataset principal
        ds = FileDataset(dicom_path, {}, file_meta=file_meta, preamble=b"\0"*128)
        
        # Adicionar metadados clínicos
        ds.PatientName = self.patient_name.get()
        ds.PatientID = self.patient_id.get()
        ds.StudyInstanceUID = generate_uid()
        ds.SeriesInstanceUID = generate_uid()
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        ds.Modality = "OT"  # Other
        ds.StudyDate = datetime.datetime.now().strftime('%Y%m%d')
        ds.ContentDate = datetime.datetime.now().strftime('%Y%m%d')
        ds.StudyTime = datetime.datetime.now().strftime('%H%M%S')
        ds.ContentTime = datetime.datetime.now().strftime('%H%M%S')
        
        # Carregar imagem JPEG
        img = Image.open(jpeg_path)
        if img.mode == 'L':
            ds.PhotometricInterpretation = "MONOCHROME2"
            ds.SamplesPerPixel = 1
            ds.BitsStored = 8
            ds.BitsAllocated = 8
            ds.HighBit = 7
            ds.PixelRepresentation = 0
        else:
            ds.PhotometricInterpretation = "RGB"
            ds.SamplesPerPixel = 3
            ds.PlanarConfiguration = 0
            ds.BitsStored = 8
            ds.BitsAllocated = 8
            ds.HighBit = 7
            ds.PixelRepresentation = 0
        
        ds.Rows = img.height
        ds.Columns = img.width
        ds.PixelData = img.tobytes()
        
        # Definir tipo de armazenamento
        ds.is_little_endian = True
        ds.is_implicit_VR = False
        
        # Salvar como DICOM
        ds.save_as(dicom_path, write_like_original=False)

if __name__ == "__main__":
    root = tk.Tk()
    app = DICOMConverterApp(root)
    root.mainloop()