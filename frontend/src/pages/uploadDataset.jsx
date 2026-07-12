import { useState } from "react";
import { uploadDataset } from "../services/api";

function UploadDataset() {
  const [file, setFile] = useState(null);

  const handleUpload = async (e) => {
    e.preventDefault();

    if (!file) {
      alert("Please select a dataset file");
      return;
    }

    const result = await uploadDataset(file);
    alert(result.message);
  };

  return (
    <form onSubmit={handleUpload}>
      <h2>Upload Dataset</h2>

      <input
        type="file"
        accept=".csv,.txt,.tsv,.xls,.xlsx,.json,.parquet,.html,.htm,.xml,.feather,.sas7bdat,.dta,.sav"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <button type="submit">Upload</button>
    </form>
  );
}

export default UploadDataset;